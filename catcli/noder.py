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
from pyfzf.pyfzf import FzfPrompt  # type: ignore

# local imports
from catcli import cnode
from catcli.cnode import Node
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
    def get_storage_names(top: Node) -> List[str]:
        """return a list of all storage names"""
        return [x.name for x in list(top.children)]

    def get_storage_node(self, top: Node,
                         name: str,
                         newpath: str = '') -> Node:
        """
        return the storage node if any
        if newpath is submitted, it will update the media info
        """
        found = None
        for node in top.children:
            if node.type != cnode.TYPE_STORAGE:
                continue
            if node.name == name:
                found = node
                break
        if found and newpath and os.path.exists(newpath):
            found.free = shutil.disk_usage(newpath).free
            found.total = shutil.disk_usage(newpath).total
            found.ts = int(time.time())
        return cast(Node, found)

    @staticmethod
    def get_node(top: Node,
                 path: str,
                 quiet: bool = False) -> Optional[Node]:
        """get the node by internal tree path"""
        resolv = anytree.resolver.Resolver('name')
        try:
            bpath = os.path.basename(path)
            the_node = resolv.get(top, bpath)
            return cast(Node, the_node)
        except anytree.resolver.ChildResolverError:
            if not quiet:
                Logger.err(f'No node at path \"{bpath}\"')
            return None

    def get_node_if_changed(self,
                            top: Node,
                            path: str,
                            treepath: str) -> Tuple[Optional[Node], bool]:
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

    def rec_size(self, node: Node,
                 store: bool = True) -> float:
        """
        recursively traverse tree and return size
        @store: store the size in the node
        """
        if node.type == cnode.TYPE_FILE:
            self._debug(f'getting node size for \"{node.name}\"')
            return float(node.size)
        msg = f'getting node size recursively for \"{node.name}\"'
        self._debug(msg)
        size: float = 0
        for i in node.children:
            if node.type == cnode.TYPE_DIR:
                size = self.rec_size(i, store=store)
                if store:
                    i.size = size
                size += size
            if node.type == cnode.TYPE_STORAGE:
                size = self.rec_size(i, store=store)
                if store:
                    i.size = size
                size += size
            else:
                continue
        if store:
            node.size = size
        return size

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
    def new_top_node(self) -> Node:
        """create a new top node"""
        return Node(cnode.NAME_TOP,
                    cnode.TYPE_TOP)

    def new_file_node(self, name: str, path: str,
                      parent: Node, storagepath: str) -> Optional[Node]:
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
        node = self._new_generic_node(name, cnode.TYPE_FILE,
                                      relpath, parent,
                                      size=stat.st_size,
                                      md5=md5,
                                      maccess=maccess)
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
                     parent: Node, storagepath: str) -> Node:
        """create a new node representing a directory"""
        path = os.path.abspath(path)
        relpath = os.sep.join([storagepath, name])
        maccess = os.path.getmtime(path)
        return self._new_generic_node(name, cnode.TYPE_DIR, relpath,
                                      parent, maccess=maccess)

    def new_storage_node(self, name: str,
                         path: str,
                         parent: str,
                         attrs: str = '') -> Node:
        """create a new node representing a storage"""
        path = os.path.abspath(path)
        free = shutil.disk_usage(path).free
        total = shutil.disk_usage(path).total
        epoch = int(time.time())
        return Node(name=name,
                    type=cnode.TYPE_STORAGE,
                    free=free,
                    total=total,
                    parent=parent,
                    attr=attrs,
                    indexed_dt=epoch)

    def new_archive_node(self, name: str, path: str,
                         parent: str, archive: str) -> Node:
        """create a new node for archive data"""
        return Node(name=name, type=cnode.TYPE_ARC, relpath=path,
                    parent=parent, size=0, md5='',
                    archive=archive)

    @staticmethod
    def _new_generic_node(name: str,
                          nodetype: str,
                          relpath: str,
                          parent: Node,
                          size: float = 0,
                          md5: str = '',
                          maccess: float = 0) -> Node:
        """generic node creation"""
        return Node(name,
                    nodetype,
                    size=size,
                    relpath=relpath,
                    md5=md5,
                    maccess=maccess,
                    parent=parent)

    ###############################################################
    # node management
    ###############################################################
    def update_metanode(self, top: Node) -> Node:
        """create or update meta node information"""
        meta = self._get_meta_node(top)
        epoch = int(time.time())
        if not meta:
            attrs: Dict[str, Any] = {}
            attrs['created'] = epoch
            attrs['created_version'] = VERSION
            meta = Node(name=cnode.NAME_META,
                        type=cnode.TYPE_META,
                        attr=self.attrs_to_string(attrs))
        if meta.attr:
            meta.attr += ', '
        meta.attr += f'access={epoch}'
        meta.attr += ', '
        meta.attr += f'access_version={VERSION}'
        return meta

    def _get_meta_node(self, top: Node) -> Optional[Node]:
        """return the meta node if any"""
        try:
            found = next(filter(lambda x: x.type == cnode.TYPE_META,
                         top.children))
            return cast(Node, found)
        except StopIteration:
            return None

    def clean_not_flagged(self, top: Node) -> int:
        """remove any node not flagged and clean flags"""
        cnt = 0
        for node in anytree.PreOrderIter(top):
            if node.type not in [cnode.TYPE_FILE, cnode.TYPE_DIR]:
                continue
            if self._clean(node):
                cnt += 1
        return cnt

    def _clean(self, node: Node) -> bool:
        """remove node if not flagged"""
        if not node.flagged():
            node.parent = None
            return True
        node.unflag()
        return False

    ###############################################################
    # printing
    ###############################################################
    def _node_to_csv(self, node: Node,
                     sep: str = ',',
                     raw: bool = False) -> None:
        """
        print a node to csv
        @node: the node to consider
        @sep: CSV separator character
        @raw: print raw size rather than human readable
        """
        if not cnode:
            return
        if node.type == node.TYPE_TOP:
            return

        out = []
        if node.type == node.TYPE_STORAGE:
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

            out.append(size_to_str(node.size, raw=raw))  # size
            out.append(epoch_to_str(storage.ts))  # indexed_at
            if self._has_attr(node, 'maccess'):
                out.append(epoch_to_str(node.maccess))  # maccess
            else:
                out.append('')  # fake maccess
            if node.md5:
                out.append(node.md5)  # md5
            else:
                out.append('')  # fake md5
            if node.type == cnode.TYPE_DIR:
                out.append(str(len(node.children)))  # nbfiles
            else:
                out.append('')  # fake nbfiles
            out.append('')  # fake free_space
            out.append('')  # fake total_space
            out.append('')  # fake meta

        line = sep.join(['"' + o + '"' for o in out])
        if len(line) > 0:
            Logger.stdout_nocolor(line)

    def _print_node_native(self, node: Node,
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
        if node.type == cnode.TYPE_TOP:
            # top node
            Logger.stdout_nocolor(f'{pre}{node.name}')
        elif node.type == cnode.TYPE_FILE:
            # node of type file
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
            size = size_to_str(node.size, raw=raw)
            compl = f'size:{size}{attr_str}'
            if withstorage:
                content = Logger.get_bold_text(storage.name)
                compl += f', storage:{content}'
            NodePrinter.print_file_native(pre, name, compl)
        elif node.type == cnode.TYPE_DIR:
            # node of type directory
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
            if node.size:
                attr.append(('totsize', size_to_str(node.size, raw=raw)))
            if withstorage:
                attr.append(('storage', Logger.get_bold_text(storage.name)))
            NodePrinter.print_dir_native(pre, name, depth=depth, attr=attr)
        elif node.type == cnode.TYPE_STORAGE:
            # node of type storage
            sztotal = size_to_str(node.total, raw=raw)
            szused = size_to_str(node.total - node.free, raw=raw)
            nbchildren = len(node.children)
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
        elif node.type == cnode.TYPE_ARC:
            # archive node
            if self.arc:
                NodePrinter.print_archive_native(pre, node.name, node.archive)
        else:
            Logger.err(f'bad node encountered: {node}')

    def print_tree(self, node: Node,
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

    def _to_csv(self, node: Node,
                raw: bool = False) -> None:
        """print the tree to csv"""
        rend = anytree.RenderTree(node, childiter=self._sort_tree)
        for _, _, item in rend:
            self._node_to_csv(item, raw=raw)

    @staticmethod
    def _fzf_prompt(strings: Any) -> Any:
        # prompt with fzf
        fzf = FzfPrompt()
        selected = fzf.prompt(strings)
        return selected

    def _to_fzf(self, node: Node, fmt: str) -> None:
        """
        fzf prompt with list and print selected node(s)
        @node: node to start with
        @fmt: output format for selected nodes
        """
        rendered = anytree.RenderTree(node, childiter=self._sort_tree)
        nodes = {}
        # construct node names list
        for _, _, rend in rendered:
            if not rend:
                continue
            parents = self._get_parents(rend)
            storage = self._get_storage(rend)
            fullpath = os.path.join(storage.name, parents)
            nodes[fullpath] = rend
        # prompt with fzf
        paths = self._fzf_prompt(nodes.keys())
        # print the resulting tree
        subfmt = fmt.replace('fzf-', '')
        for path in paths:
            if not path:
                continue
            if path not in nodes:
                continue
            rend = nodes[path]
            self.print_tree(rend, fmt=subfmt)

    @staticmethod
    def to_dot(node: Node,
               path: str = 'tree.dot') -> str:
        """export to dot for graphing"""
        anytree.exporter.DotExporter(node).to_dotfile(path)
        Logger.info(f'dot file created under \"{path}\"')
        return f'dot {path} -T png -o /tmp/tree.png'

    ###############################################################
    # searching
    ###############################################################
    def find_name(self, top: Node,
                  key: str,
                  script: bool = False,
                  only_dir: bool = False,
                  startnode: Optional[Node] = None,
                  parentfromtree: bool = False,
                  fmt: str = 'native',
                  raw: bool = False) -> List[Node]:
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
        start: Optional[Node] = top
        if startnode:
            start = self.get_node(top, startnode)
        filterfunc = self._callback_find_name(key, only_dir)
        found = anytree.findall(start, filter_=filterfunc)
        nbfound = len(found)
        self._debug(f'found {nbfound} node(s)')

        # compile found nodes
        paths = {}
        for item in found:
            item = self._sanitize(item)
            if parentfromtree:
                paths[self._get_parents(item)] = item
            else:
                paths[item.relpath] = item

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
        def find_name(node: Node) -> bool:
            if node.type == cnode.TYPE_STORAGE:
                # ignore storage nodes
                return False
            if node.type == cnode.TYPE_TOP:
                # ignore top nodes
                return False
            if node.type == cnode.TYPE_META:
                # ignore meta nodes
                return False
            if only_dir and node.type != cnode.TYPE_DIR:
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
    def list(self, top: Node,
             path: str,
             rec: bool = False,
             fmt: str = 'native',
             raw: bool = False) -> List[Node]:
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
                   top: Node,
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

    def list_to_tree(self, parent: Node, names: List[str]) -> None:
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
                   items: List[Node]) -> List[Node]:
        """sorting a list of items"""
        return sorted(items, key=self._sort, reverse=self.sortsize)

    def _sort(self, lst: Node) -> Any:
        """sort a list"""
        if self.sortsize:
            return self._sort_size(lst)
        return self._sort_fs(lst)

    @staticmethod
    def _sort_fs(node: Node) -> Tuple[str, str]:
        """sorting nodes dir first and alpha"""
        return (node.type, node.name.lstrip('.').lower())

    @staticmethod
    def _sort_size(node: Node) -> float:
        """sorting nodes by size"""
        try:
            if not node.size:
                return 0
            return float(node.size)
        except AttributeError:
            return 0

    def _get_storage(self, node: Node) -> Node:
        """recursively traverse up to find storage"""
        if node.type == cnode.TYPE_STORAGE:
            return node
        return cast(Node, node.ancestors[1])

    @staticmethod
    def _has_attr(node: Node, attr: str) -> bool:
        """return True if node has attr as attribute"""
        return attr in node.__dict__.keys()

    def _get_parents(self, node: Node) -> str:
        """get all parents recursively"""
        if node.type == cnode.TYPE_STORAGE:
            return ''
        if node.type == cnode.TYPE_TOP:
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

    @staticmethod
    def _sanitize(node: Node) -> Node:
        """sanitize node strings"""
        node.name = fix_badchars(node.name)
        node.relpath = fix_badchars(node.relpath)
        return node

    def _debug(self, string: str) -> None:
        """print debug"""
        if not self.debug:
            return
        Logger.debug(string)
