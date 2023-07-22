"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Class that process nodes in the catalog tree
"""

import os
import shutil
import time
from typing import List, Union, Tuple, Any, Optional, Dict, cast
import anytree  # type: ignore

# local imports
from catcli import nodes
from catcli.nodes import NodeAny, NodeStorage, \
    NodeTop, NodeFile, NodeArchived, NodeDir, NodeMeta, \
    typcast_node
from catcli.utils import size_to_str, epoch_to_str, md5sum, fix_badchars
from catcli.logger import Logger
from catcli.nodeprinter import NodePrinter
from catcli.decomp import Decomp
from catcli.version import __version__ as VERSION
from catcli.exceptions import CatcliException


class Noder:
    """
    handles node in the catalog tree
    There are 4 types of node:
    * "top" node representing the top node (generic node)
    * "storage" node representing a storage
    * "dir" node representing a directory
    * "file" node representing a file
    """

    CSV_HEADER = ('name,type,path,size,indexed_at,'
                  'maccess,md5,nbfiles,free_space,'
                  'total_space,meta')

    def __init__(self, debug: bool = False,
                 sortsize: bool = False,
                 arc: bool = False) -> None:
        """
        @debug: debug mode
        @sortsize: sort nodes by size
        @arch: handle archive
        """
        self.hash = True
        self.debug = debug
        self.sortsize = sortsize
        self.arc = arc
        if self.arc:
            self.decomp = Decomp()

    @staticmethod
    def get_storage_names(top: NodeTop) -> List[str]:
        """return a list of all storage names"""
        return [x.name for x in list(top.children)]

    def get_storage_node(self, top: NodeTop,
                         name: str,
                         newpath: str = '') -> NodeStorage:
        """
        return the storage node if any
        if newpath is submitted, it will update the media info
        """
        found = None
        for node in top.children:
            if node.type != nodes.TYPE_STORAGE:
                continue
            if node.name == name:
                found = node
                break
        if found and newpath and os.path.exists(newpath):
            found.free = shutil.disk_usage(newpath).free
            found.total = shutil.disk_usage(newpath).total
            found.ts = int(time.time())
        return cast(NodeStorage, found)

    @staticmethod
    def get_node(top: NodeTop,
                 path: str,
                 quiet: bool = False) -> Optional[NodeAny]:
        """get the node by internal tree path"""
        resolv = anytree.resolver.Resolver('name')
        try:
            bpath = os.path.basename(path)
            the_node = resolv.get(top, bpath)
            typcast_node(the_node)
            return cast(NodeAny, the_node)
        except anytree.resolver.ChildResolverError:
            if not quiet:
                Logger.err(f'No node at path \"{bpath}\"')
            return None

    def get_node_if_changed(self,
                            top: NodeTop,
                            path: str,
                            treepath: str) -> Tuple[Optional[NodeAny], bool]:
        """
        return the node (if any) and if it has changed
        @top: top node (storage)
        @path: abs path to file
        @treepath: rel path from indexed directory
        """
        treepath = treepath.lstrip(os.sep)
        node = self.get_node(top, treepath, quiet=True)
        # node does not exist
        if not node:
            self._debug('\tchange: node does not exist')
            return None, True
        if os.path.isdir(path):
            return node, False
        # force re-indexing if no maccess
        maccess = os.path.getmtime(path)
        if not self._has_attr(node, 'maccess') or \
                not node.maccess:
            self._debug('\tchange: no maccess found')
            return node, True
        # maccess changed
        old_maccess = node.maccess
        if float(maccess) != float(old_maccess):
            self._debug(f'\tchange: maccess changed for \"{path}\"')
            return node, True
        # test hash
        if self.hash and node.md5:
            md5 = self._get_hash(path)
            if md5 and md5 != node.md5:
                msg = f'\tchange: checksum changed for \"{path}\"'
                self._debug(msg)
                return node, True
        self._debug(f'\tchange: no change for \"{path}\"')
        return node, False

    def rec_size(self, node: Union[NodeDir, NodeStorage],
                 store: bool = True) -> int:
        """
        recursively traverse tree and return size
        @store: store the size in the node
        """
        if node.type == nodes.TYPE_FILE:
            node.__class__ = NodeFile
            msg = f'size of {node.type} \"{node.name}\": {node.nodesize}'
            self._debug(msg)
            return node.nodesize
        msg = f'getting node size recursively for \"{node.name}\"'
        self._debug(msg)
        fullsize: int = 0
        for i in node.children:
            if node.type == nodes.TYPE_DIR:
                sub_size = self.rec_size(i, store=store)
                if store:
                    i.nodesize = sub_size
                fullsize += sub_size
                continue
            if node.type == nodes.TYPE_STORAGE:
                sub_size = self.rec_size(i, store=store)
                if store:
                    i.nodesize = sub_size
                fullsize += sub_size
                continue
            self._debug(f'skipping {node.name}')
        if store:
            node.nodesize = fullsize
        self._debug(f'size of {node.type} \"{node.name}\": {fullsize}')
        return fullsize

    ###############################################################
    # public helpers
    ###############################################################
    @staticmethod
    def attrs_to_string(attr: Union[List[str], Dict[str, str], str]) -> str:
        """format the storage attr for saving"""
        if not attr:
            return ''
        if isinstance(attr, list):
            return ', '.join(attr)
        if isinstance(attr, dict):
            ret = []
            for key, val in attr.items():
                ret.append(f'{key}={val}')
            return ', '.join(ret)
        attr = attr.rstrip()
        return attr

    def do_hashing(self, val: bool) -> None:
        """hash files when indexing"""
        self.hash = val

    ###############################################################
    # node creation
    ###############################################################
    def new_top_node(self) -> NodeTop:
        """create a new top node"""
        top = NodeTop(nodes.NAME_TOP)
        self._debug(f'new top node: {top}')
        return top

    def new_file_node(self, name: str, path: str,
                      parent: NodeAny, storagepath: str) -> Optional[NodeFile]:
        """create a new node representing a file"""
        if not os.path.exists(path):
            Logger.err(f'File \"{path}\" does not exist')
            return None
        path = os.path.abspath(path)
        try:
            stat = os.lstat(path)
        except OSError as exc:
            Logger.err(f'OSError: {exc}')
            return None
        md5 = ''
        if self.hash:
            md5 = self._get_hash(path)
        relpath = os.sep.join([storagepath, name])

        maccess = os.path.getmtime(path)
        node = NodeFile(name,
                        relpath,
                        stat.st_size,
                        md5,
                        maccess,
                        parent=parent)
        if self.arc:
            ext = os.path.splitext(path)[1][1:]
            if ext.lower() in self.decomp.get_formats():
                self._debug(f'{path} is an archive')
                names = self.decomp.get_names(path)
                self.list_to_tree(node, names)
            else:
                self._debug(f'{path} is NOT an archive')
        return node

    def new_dir_node(self, name: str, path: str,
                     parent: NodeAny, storagepath: str) -> NodeDir:
        """create a new node representing a directory"""
        path = os.path.abspath(path)
        relpath = os.sep.join([storagepath, name])
        maccess = os.path.getmtime(path)
        return NodeDir(name,
                       relpath,
                       0,
                       maccess,
                       parent=parent)

    def new_storage_node(self, name: str,
                         path: str,
                         parent: str,
                         attrs: Dict[str, Any]) \
            -> NodeStorage:
        """create a new node representing a storage"""
        path = os.path.abspath(path)
        free = shutil.disk_usage(path).free
        total = shutil.disk_usage(path).total
        epoch = int(time.time())
        return NodeStorage(name,
                           free,
                           total,
                           0,
                           epoch,
                           self.attrs_to_string(attrs),
                           parent=parent)

    def new_archive_node(self, name: str, path: str,
                         parent: str, archive: str) -> NodeArchived:
        """create a new node for archive data"""
        return NodeArchived(name=name, relpath=path,
                            parent=parent, nodesize=0, md5='',
                            archive=archive)

    ###############################################################
    # node management
    ###############################################################
    def update_metanode(self, top: NodeTop) -> NodeMeta:
        """create or update meta node information"""
        meta = self._get_meta_node(top)
        epoch = int(time.time())
        if not meta:
            attrs: Dict[str, Any] = {}
            attrs['created'] = epoch
            attrs['created_version'] = VERSION
            meta = NodeMeta(name=nodes.NAME_META,
                            attr=attrs)
        meta.attr['access'] = epoch
        meta.attr['access_version'] = VERSION
        return meta

    def _get_meta_node(self, top: NodeTop) -> Optional[NodeMeta]:
        """return the meta node if any"""
        try:
            found = next(filter(lambda x: x.type == nodes.TYPE_META,
                         top.children))
            return cast(NodeMeta, found)
        except StopIteration:
            return None

    def clean_not_flagged(self, top: NodeTop) -> int:
        """remove any node not flagged and clean flags"""
        cnt = 0
        for node in anytree.PreOrderIter(top):
            typcast_node(node)
            if node.type not in [nodes.TYPE_DIR, nodes.TYPE_FILE]:
                continue
            if self._clean(node):
                cnt += 1
        return cnt

    def _clean(self, node: NodeAny) -> bool:
        """remove node if not flagged"""
        if not node.flagged():
            node.parent = None
            return True
        node.unflag()
        return False

    ###############################################################
    # printing
    ###############################################################
    def _node_to_csv(self, node: NodeAny,
                     sep: str = ',',
                     raw: bool = False) -> None:
        """
        print a node to csv
        @node: the node to consider
        @sep: CSV separator character
        @raw: print raw size rather than human readable
        """
        if not node:
            return
        if node.type == nodes.TYPE_TOP:
            return

        out = []
        if node.type == nodes.TYPE_STORAGE:
            # handle storage
            out.append(node.name)   # name
            out.append(node.type)   # type
            out.append('')          # fake full path
            size = self.rec_size(node, store=False)
            out.append(size_to_str(size, raw=raw))  # size
            out.append(epoch_to_str(node.ts))  # indexed_at
            out.append('')  # fake maccess
            out.append('')  # fake md5
            out.append(str(len(node.children)))  # nbfiles
            # fake free_space
            out.append(size_to_str(node.free, raw=raw))
            # fake total_space
            out.append(size_to_str(node.total, raw=raw))
            out.append(node.attr)  # meta
        else:
            # handle other nodes
            out.append(node.name.replace('"', '""'))  # name
            out.append(node.type)  # type
            parents = self._get_parents(node)
            storage = self._get_storage(node)
            fullpath = os.path.join(storage.name, parents)
            out.append(fullpath.replace('"', '""'))  # full path

            out.append(size_to_str(node.nodesize, raw=raw))  # size
            out.append(epoch_to_str(storage.ts))  # indexed_at
            if self._has_attr(node, 'maccess'):
                out.append(epoch_to_str(node.maccess))  # maccess
            else:
                out.append('')  # fake maccess
            if self._has_attr(node, 'md5'):
                out.append(node.md5)  # md5
            else:
                out.append('')  # fake md5
            if node.type == nodes.TYPE_DIR:
                out.append(str(len(node.children)))  # nbfiles
            else:
                out.append('')  # fake nbfiles
            out.append('')  # fake free_space
            out.append('')  # fake total_space
            out.append('')  # fake meta

        line = sep.join(['"' + o + '"' for o in out])
        if len(line) > 0:
            Logger.stdout_nocolor(line)

    def _print_node_native(self, node: NodeAny,
                           pre: str = '',
                           withpath: bool = False,
                           withdepth: bool = False,
                           withstorage: bool = False,
                           recalcparent: bool = False,
                           raw: bool = False) -> None:
        """
        print a node
        @node: the node to print
        @pre: string to print before node
        @withpath: print the node path
        @withdepth: print the node depth info
        @withstorage: print the node storage it belongs to
        @recalcparent: get relpath from tree instead of relpath field
        @raw: print raw size rather than human readable
        """
        if node.type == nodes.TYPE_TOP:
            # top node
            node.__class__ = NodeTop
            Logger.stdout_nocolor(f'{pre}{node.name}')
        elif node.type == nodes.TYPE_FILE:
            # node of type file
            node.__class__ = NodeFile
            name = node.name
            if withpath:
                if recalcparent:
                    name = os.sep.join([self._get_parents(node.parent), name])
                else:
                    name = node.relpath
            name = name.lstrip(os.sep)
            if withstorage:
                storage = self._get_storage(node)
            attr_str = ''
            if node.md5:
                attr_str = f', md5:{node.md5}'
            size = size_to_str(node.nodesize, raw=raw)
            compl = f'size:{size}{attr_str}'
            if withstorage:
                content = Logger.get_bold_text(storage.name)
                compl += f', storage:{content}'
            NodePrinter.print_file_native(pre, name, compl)
        elif node.type == nodes.TYPE_DIR:
            # node of type directory
            node.__class__ = NodeDir
            name = node.name
            if withpath:
                if recalcparent:
                    name = os.sep.join([self._get_parents(node.parent), name])
                else:
                    name = node.relpath
            name = name.lstrip(os.sep)
            depth = 0
            if withdepth:
                depth = len(node.children)
            if withstorage:
                storage = self._get_storage(node)
            attr: List[Tuple[str, str]] = []
            if node.nodesize:
                attr.append(('totsize', size_to_str(node.nodesize, raw=raw)))
            if withstorage:
                attr.append(('storage', Logger.get_bold_text(storage.name)))
            NodePrinter.print_dir_native(pre, name, depth=depth, attr=attr)
        elif node.type == nodes.TYPE_STORAGE:
            # node of type storage
            node.__class__ = NodeStorage
            sztotal = size_to_str(node.total, raw=raw)
            szused = size_to_str(node.total - node.free, raw=raw)
            nbchildren = len(node.children)
            pcent = 0
            if node.total > 0:
                pcent = node.free * 100 / node.total
            freepercent = f'{pcent:.1f}%'
            # get the date
            timestamp = ''
            if self._has_attr(node, 'ts'):
                timestamp = 'date:'
                timestamp += epoch_to_str(node.ts)
            disksize = ''
            # the children size
            recsize = self.rec_size(node, store=False)
            sizestr = size_to_str(recsize, raw=raw)
            disksize = 'totsize:' + f'{sizestr}'
            # format the output
            name = node.name
            args = [
                'nbfiles:' + f'{nbchildren}',
                disksize,
                f'free:{freepercent}',
                'du:' + f'{szused}/{sztotal}',
                timestamp]
            argsstring = ' | '.join(args)
            NodePrinter.print_storage_native(pre,
                                             name,
                                             argsstring,
                                             node.attr)
        elif node.type == nodes.TYPE_ARCHIVED:
            # archive node
            node.__class__ = NodeArchived
            if self.arc:
                NodePrinter.print_archive_native(pre, node.name, node.archive)
        else:
            Logger.err(f'bad node encountered: {node}')

    def print_tree(self, node: NodeAny,
                   fmt: str = 'native',
                   raw: bool = False) -> None:
        """
        print the tree in different format
        @node: start node
        @style: when fmt=native, defines the tree style
        @fmt: output format
        @raw: print the raw size rather than human readable
        """
        if fmt == 'native':
            # "tree" style
            rend = anytree.RenderTree(node, childiter=self._sort_tree)
            for pre, _, thenode in rend:
                self._print_node_native(thenode, pre=pre,
                                        withdepth=True, raw=raw)
        elif fmt == 'csv':
            # csv output
            self._to_csv(node, raw=raw)
        elif fmt == 'csv-with-header':
            # csv output
            Logger.stdout_nocolor(self.CSV_HEADER)
            self._to_csv(node, raw=raw)

    def _to_csv(self, node: NodeAny,
                raw: bool = False) -> None:
        """print the tree to csv"""
        rend = anytree.RenderTree(node, childiter=self._sort_tree)
        for _, _, item in rend:
            self._node_to_csv(item, raw=raw)

    @staticmethod
    def _fzf_prompt(strings: Any) -> Any:
        """prompt with fzf"""
        try:
            from pyfzf.pyfzf import FzfPrompt  # type: ignore # pylint: disable=C0415 # noqa
            fzf = FzfPrompt()
            selected = fzf.prompt(strings)
            return selected
        except ModuleNotFoundError:
            Logger.err('install pyfzf to use fzf')
            return None

    def _to_fzf(self, node: NodeAny, fmt: str) -> None:
        """
        fzf prompt with list and print selected node(s)
        @node: node to start with
        @fmt: output format for selected nodes
        """
        rendered = anytree.RenderTree(node, childiter=self._sort_tree)
        the_nodes = {}
        # construct node names list
        for _, _, rend in rendered:
            if not rend:
                continue
            parents = self._get_parents(rend)
            storage = self._get_storage(rend)
            fullpath = os.path.join(storage.name, parents)
            the_nodes[fullpath] = rend
        # prompt with fzf
        paths = self._fzf_prompt(the_nodes.keys())
        # print the resulting tree
        subfmt = fmt.replace('fzf-', '')
        for path in paths:
            if not path:
                continue
            if path not in the_nodes:
                continue
            rend = the_nodes[path]
            self.print_tree(rend, fmt=subfmt)

    @staticmethod
    def to_dot(top: NodeTop,
               path: str = 'tree.dot') -> str:
        """export to dot for graphing"""
        anytree.exporter.DotExporter(top).to_dotfile(path)
        Logger.info(f'dot file created under \"{path}\"')
        return f'dot {path} -T png -o /tmp/tree.png'

    ###############################################################
    # searching
    ###############################################################
    def find_name(self, top: NodeTop,
                  key: str,
                  script: bool = False,
                  only_dir: bool = False,
                  startnode: Optional[NodeAny] = None,
                  parentfromtree: bool = False,
                  fmt: str = 'native',
                  raw: bool = False) -> List[NodeAny]:
        """
        find files based on their names
        @top: top node
        @key: term to search for
        @script: output script
        @directory: only search for directories
        @startpath: node to start with
        @parentfromtree: get path from parent instead of stored relpath
        @fmt: output format
        @raw: raw size output
        returns the found nodes
        """
        self._debug(f'searching for \"{key}\"')

        # search for nodes based on path
        start: Optional[NodeAny] = top
        if startnode:
            start = self.get_node(top, startnode)
        filterfunc = self._callback_find_name(key, only_dir)
        found = anytree.findall(start, filter_=filterfunc)
        self._debug(f'found {len(found)} node(s)')

        # compile found nodes
        paths = {}
        for item in found:
            item.name = fix_badchars(item.name)
            if hasattr(item, 'relpath'):
                item.relpath = fix_badchars(item.relpath)
            storage = self._get_storage(item)
            if parentfromtree:
                parent = self._get_parents(item)
                key = f'{storage}/{parent}/{item.relpath}'
                paths[parent] = item
            else:
                key = f'{storage}/{item.path}'
                paths[key] = item

        # handle fzf mode
        if fmt.startswith('fzf'):
            selected = self._fzf_prompt(paths.keys())
            newpaths = {}
            subfmt = fmt.replace('fzf-', '')
            for item in selected:
                if item not in paths:
                    continue
                newpaths[item] = paths[item]
                self.print_tree(newpaths[item], fmt=subfmt)
            paths = newpaths
        else:
            if fmt == 'native':
                for _, item in paths.items():
                    self._print_node_native(item, withpath=True,
                                            withdepth=True,
                                            withstorage=True,
                                            recalcparent=parentfromtree,
                                            raw=raw)
            elif fmt.startswith('csv'):
                if fmt == 'csv-with-header':
                    Logger.stdout_nocolor(self.CSV_HEADER)
                for _, item in paths.items():
                    self._node_to_csv(item, raw=raw)

        # execute script if any
        if script:
            tmp = ['${source}/' + x for x in paths]
            tmpstr = ' '.join(tmp)
            cmd = f'op=file; source=/media/mnt; $op {tmpstr}'
            Logger.info(cmd)

        return list(paths.values())

    def _callback_find_name(self, term: str, only_dir: bool) -> Any:
        """callback for finding files"""
        def find_name(node: NodeAny) -> bool:
            if node.type == nodes.TYPE_STORAGE:
                # ignore storage nodes
                return False
            if node.type == nodes.TYPE_TOP:
                # ignore top nodes
                return False
            if node.type == nodes.TYPE_META:
                # ignore meta nodes
                return False
            if only_dir and node.type == nodes.TYPE_DIR:
                # ignore non directory
                return False

            # filter
            if not term:
                return True
            if term.lower() in node.name.lower():
                return True

            # ignore
            return False
        return find_name

    ###############################################################
    # ls
    ###############################################################
    def list(self, top: NodeTop,
             path: str,
             rec: bool = False,
             fmt: str = 'native',
             raw: bool = False) -> List[NodeAny]:
        """
        list nodes for "ls"
        @top: top node
        @path: path to search for
        @rec: recursive walk
        @fmt: output format
        @raw: print raw size
        """
        self._debug(f'walking path: \"{path}\" from {top}')

        resolv = anytree.resolver.Resolver('name')
        found = []
        try:
            # resolve the path in the tree
            found = resolv.glob(top, path)
            if len(found) < 1:
                # nothing found
                self._debug('nothing found')
                return []

            if rec:
                # print the entire tree
                self.print_tree(found[0].parent, fmt=fmt, raw=raw)
                return found

            # sort found nodes
            found = sorted(found, key=self._sort, reverse=self.sortsize)

            # print the parent
            if fmt == 'native':
                self._print_node_native(found[0].parent,
                                        withpath=False,
                                        withdepth=True,
                                        raw=raw)
            elif fmt.startswith('csv'):
                self._node_to_csv(found[0].parent, raw=raw)
            elif fmt.startswith('fzf'):
                pass

            # print all found nodes
            if fmt == 'csv-with-header':
                Logger.stdout_nocolor(self.CSV_HEADER)
            for item in found:
                if fmt == 'native':
                    self._print_node_native(item, withpath=False,
                                            pre='- ',
                                            withdepth=True,
                                            raw=raw)
                elif fmt.startswith('csv'):
                    self._node_to_csv(item, raw=raw)
                elif fmt.startswith('fzf'):
                    self._to_fzf(item, fmt)

        except anytree.resolver.ChildResolverError:
            pass
        return found

    ###############################################################
    # tree creation
    ###############################################################
    def _add_entry(self, name: str,
                   top: NodeTop,
                   resolv: Any) -> None:
        """add an entry to the tree"""
        entries = name.rstrip(os.sep).split(os.sep)
        if len(entries) == 1:
            self.new_archive_node(name, name, top, top.name)
            return
        sub = os.sep.join(entries[:-1])
        nodename = entries[-1]
        try:
            parent = resolv.get(top, sub)
            parent = self.new_archive_node(nodename, name, parent, top.name)
        except anytree.resolver.ChildResolverError:
            self.new_archive_node(nodename, name, top, top.name)

    def list_to_tree(self, parent: NodeAny, names: List[str]) -> None:
        """convert list of files to a tree"""
        if not names:
            return
        resolv = anytree.resolver.Resolver('name')
        for name in names:
            name = name.rstrip(os.sep)
            self._add_entry(name, parent, resolv)

    ###############################################################
    # diverse
    ###############################################################
    def _sort_tree(self,
                   items: List[NodeAny]) -> List[NodeAny]:
        """sorting a list of items"""
        return sorted(items, key=self._sort, reverse=self.sortsize)

    def _sort(self, lst: NodeAny) -> Any:
        """sort a list"""
        if self.sortsize:
            return self._sort_size(lst)
        return self._sort_fs(lst)

    @staticmethod
    def _sort_fs(node: NodeAny) -> Tuple[str, str]:
        """sorting nodes dir first and alpha"""
        return (node.type, node.name.lstrip('.').lower())

    @staticmethod
    def _sort_size(node: NodeAny) -> float:
        """sorting nodes by size"""
        try:
            if not node.nodesize:
                return 0
            return float(node.nodesize)
        except AttributeError:
            return 0

    def _get_storage(self, node: NodeAny) -> NodeStorage:
        """recursively traverse up to find storage"""
        if node.type == nodes.TYPE_STORAGE:
            return node
        return cast(NodeStorage, node.ancestors[1])

    @staticmethod
    def _has_attr(node: NodeAny, attr: str) -> bool:
        """return True if node has attr as attribute"""
        return attr in node.__dict__.keys()

    def _get_parents(self, node: NodeAny) -> str:
        """get all parents recursively"""
        if node.type == nodes.TYPE_STORAGE:
            return ''
        if node.type == nodes.TYPE_TOP:
            return ''
        parent = self._get_parents(node.parent)
        if parent:
            return os.sep.join([parent, node.name])
        return str(node.name)

    @staticmethod
    def _get_hash(path: str) -> str:
        """return md5 hash of node"""
        try:
            return md5sum(path)
        except CatcliException as exc:
            Logger.err(str(exc))
            return ''

    def _debug(self, string: str) -> None:
        """print debug"""
        if not self.debug:
            return
        Logger.debug(string)
