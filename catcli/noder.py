"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Class that process nodes in the catalog tree
"""

import os
import shutil
import time
from typing import List, Union, Tuple, Any, Optional, Dict, cast
import fnmatch
import anytree
from natsort import os_sort_keygen

# local imports
from catcli import nodes
from catcli.nodes import NodeAny, NodeStorage, \
    NodeTop, NodeFile, NodeArchived, NodeDir, NodeMeta, \
    typcast_node
from catcli.utils import md5sum, fix_badchars, has_attr
from catcli.logger import Logger
from catcli.printer_native import NativePrinter
from catcli.printer_csv import CsvPrinter
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
    # pylint: disable=R0904

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
        self.csv_printer = CsvPrinter()
        self.native_printer = NativePrinter()

    @staticmethod
    def get_storage_names(top: NodeTop) -> List[str]:
        """return a list of all storage names"""
        return [x.name for x in list(top.children)]

    def find_storage_node_by_name(self, top: NodeTop,
                                  name: str) -> Optional[NodeStorage]:
        """find a storage node by name"""
        for node in top.children:
            if node.type != nodes.TYPE_STORAGE:
                continue
            if node.name == name:
                return cast(NodeStorage, node)
        return None

    def update_storage_path(self, top: NodeTop,
                            name: str,
                            newpath: str) -> None:
        """find and update storage path on update"""
        storage = self.find_storage_node_by_name(top, name)
        if storage and newpath and os.path.exists(newpath):
            storage.free = shutil.disk_usage(newpath).free
            storage.total = shutil.disk_usage(newpath).total
            storage.ts = int(time.time())

    @staticmethod
    def get_node(top: NodeTop,
                 path: str,
                 quiet: bool = False) -> Optional[NodeAny]:
        """get the node by internal tree path"""
        resolv = anytree.resolver.Resolver('name')
        bpath = ''
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
        if not has_attr(node, 'maccess') or \
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
                      parent: NodeAny) -> Optional[NodeFile]:
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

        maccess = os.path.getmtime(path)
        node = NodeFile(name,
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
                     parent: NodeAny) -> NodeDir:
        """create a new node representing a directory"""
        path = os.path.abspath(path)
        maccess = os.path.getmtime(path)
        return NodeDir(name,
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

    def new_archive_node(self,
                         name: str,
                         parent: str,
                         archive: str) -> NodeArchived:
        """create a new node for archive data"""
        return NodeArchived(name=name,
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
    def _print_node_csv(self, node: NodeAny,
                        sep: str = ',',
                        raw: bool = False) -> None:
        """
        print a node to csv
        @node: the node to consider
        @sep: CSV separator character
        @raw: print raw size rather than human readable
        """
        typcast_node(node)
        if not node:
            return
        if node.type == nodes.TYPE_TOP:
            return
        if node.type == nodes.TYPE_STORAGE:
            self.csv_printer.print_storage(node,
                                           sep=sep,
                                           raw=raw)
        else:
            self.csv_printer.print_node(node,
                                        sep=sep,
                                        raw=raw)

    def _print_node_du(self, node: NodeAny,
                       raw: bool = False) -> None:
        """
        print node du style
        """
        typcast_node(node)
        thenodes = self._get_entire_tree(node,
                                         dironly=True)
        for thenode in thenodes:
            self.native_printer.print_du(thenode, raw=raw)

    def _print_node_native(self, node: NodeAny,
                           pre: str = '',
                           withpath: bool = False,
                           withnbchildren: bool = False,
                           withstorage: bool = False,
                           raw: bool = False) -> None:
        """
        print a node
        @node: the node to print
        @pre: string to print before node
        @withpath: print the node path
        @withnbchildren: print the node nb children
        @withstorage: print the node storage it belongs to
        @raw: print raw size rather than human readable
        """
        typcast_node(node)
        if node.type == nodes.TYPE_TOP:
            # top node
            self.native_printer.print_top(pre, node.name)
        elif node.type == nodes.TYPE_FILE:
            # node of type file
            self.native_printer.print_file(pre, node,
                                           withpath=withpath,
                                           withstorage=withstorage,
                                           raw=raw)
        elif node.type == nodes.TYPE_DIR:
            # node of type directory
            self.native_printer.print_dir(pre,
                                          node,
                                          withpath=withpath,
                                          withstorage=withstorage,
                                          withnbchildren=withnbchildren,
                                          raw=raw)
        elif node.type == nodes.TYPE_STORAGE:
            # node of type storage
            self.native_printer.print_storage(pre,
                                              node,
                                              raw=raw)
        elif node.type == nodes.TYPE_ARCHIVED:
            # archive node
            if self.arc:
                self.native_printer.print_archive(pre, node.name, node.archive)
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
                                        withnbchildren=True, raw=raw)
        elif fmt == 'csv':
            # csv output
            self._print_nodes_csv(node, raw=raw)
        elif fmt == 'csv-with-header':
            # csv output
            self.csv_printer.print_header()
            self._print_nodes_csv(node, raw=raw)

    def _print_nodes_csv(self, node: NodeAny,
                         raw: bool = False) -> None:
        """print the tree to csv"""
        rend = anytree.RenderTree(node, childiter=self._sort_tree)
        for _, _, item in rend:
            self._print_node_csv(item, raw=raw)

    @staticmethod
    def _fzf_prompt(strings: Any) -> Any:
        """prompt with fzf"""
        try:
            from pyfzf.pyfzf import FzfPrompt  # pylint: disable=C0415 # noqa
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
            parents = rend.get_fullpath()
            storage = rend.get_storage_node()
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
    def find(self, top: NodeTop,
             key: str,
             script: bool = False,
             only_dir: bool = False,
             startnode: Optional[NodeAny] = None,
             fmt: str = 'native',
             raw: bool = False) -> List[NodeAny]:
        """
        find files based on their names
        @top: top node
        @key: term to search for
        @script: output script
        @directory: only search for directories
        @startpath: node to start with
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
            typcast_node(item)
            item.name = fix_badchars(item.name)
            key = item.get_fullpath()
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
                    self._print_node_native(item,
                                            withpath=True,
                                            withnbchildren=True,
                                            withstorage=True,
                                            raw=raw)
            elif fmt.startswith('csv'):
                if fmt == 'csv-with-header':
                    self.csv_printer.print_header()
                for _, item in paths.items():
                    self._print_node_csv(item, raw=raw)

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
            typcast_node(node)
            path = node.get_fullpath()
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
            if term in path:
                return True
            if self.debug:
                Logger.debug(f'match \"{path}\" with \"{term}\"')
            if fnmatch.fnmatch(path, term):
                return True

            # ignore
            return False
        return find_name

    ###############################################################
    # fixsizes
    ###############################################################
    def fixsizes(self, top: NodeTop) -> None:
        """fix node sizes"""
        typcast_node(top)
        rend = anytree.RenderTree(top)
        for _, _, thenode in rend:
            typcast_node(thenode)
            thenode.nodesize = thenode.get_rec_size()

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
        self._debug(f'ls walking path: \"{path}\" from \"{top.name}\"')
        resolv = anytree.resolver.Resolver('name')
        found = []
        try:
            if '*' in path or '?' in path:
                # we need to handle glob
                self._debug('glob ls...')
                found = resolv.glob(top, path)
            else:
                # we have a canonical path
                self._debug('get ls...')
                foundone = resolv.get(top, path)
                cast(NodeAny, foundone)
                typcast_node(foundone)
                if foundone and foundone.may_have_children():
                    # let's find its children as well
                    modpath = os.path.join(path, '*')
                    found = resolv.glob(top, modpath)
                else:
                    found = [foundone]

            if len(found) < 1:
                # nothing found
                self._debug('nothing found')
                return []

            if rec:
                # print the entire tree
                self.print_tree(found[0].parent, fmt=fmt, raw=raw)
                return found

            # sort found nodes
            found = sorted(found, key=os_sort_keygen(self._sort))

            # print all found nodes
            if fmt == 'csv-with-header':
                self.csv_printer.print_header()
            for item in found:
                if fmt == 'native':
                    self._print_node_native(item,
                                            withpath=True,
                                            withnbchildren=True,
                                            raw=raw)
                elif fmt.startswith('csv'):
                    self._print_node_csv(item, raw=raw)
                elif fmt.startswith('fzf'):
                    self._to_fzf(item, fmt)

        except anytree.resolver.ChildResolverError:
            pass
        return found

    ###############################################################
    # du
    ###############################################################
    def diskusage(self, top: NodeTop,
                  path: str,
                  raw: bool = False) -> List[NodeAny]:
        """disk usage"""
        self._debug(f'du walking path: \"{path}\" from \"{top.name}\"')
        resolv = anytree.resolver.Resolver('name')
        found: NodeAny
        try:
            # we have a canonical path
            self._debug('get du...')
            found = resolv.get(top, path)
            if not found:
                # nothing found
                self._debug('nothing found')
                return []

            self._debug(f'du found: {found}')
            self._print_node_du(found, raw=raw)
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
            self.new_archive_node(name, top, top.name)
            return
        sub = os.sep.join(entries[:-1])
        nodename = entries[-1]
        try:
            parent = resolv.get(top, sub)
            parent = self.new_archive_node(nodename, parent, top.name)
        except anytree.resolver.ChildResolverError:
            self.new_archive_node(nodename, top, top.name)

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
    def _get_entire_tree(self, start: NodeAny,
                         dironly: bool = False) -> List[NodeAny]:
        """
        get entire tree and sort it
        """
        typcast_node(start)
        rend = anytree.RenderTree(start)
        thenodes = []
        if dironly:
            for _, _, thenode in rend:
                typcast_node(thenode)
                if thenode.type == nodes.TYPE_DIR:
                    thenodes.append(thenode)
        else:
            thenodes = [x for _, _, x in rend]
        return sorted(thenodes, key=os_sort_keygen(self._sort))

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
    def _sort_fs(node: NodeAny) -> str:
        """sort by name"""
        # to sort by types then name
        return str(node.name)

    @staticmethod
    def _sort_size(node: NodeAny) -> float:
        """sorting nodes by size"""
        try:
            if not node.nodesize:
                return 0
            return float(node.nodesize)
        except AttributeError:
            return 0

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
