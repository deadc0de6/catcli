"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Class that represents a node in the catalog tree
"""

import os
import shutil
import time
import anytree
from pyfzf.pyfzf import FzfPrompt

# local imports
from catcli.utils import size_to_str, epoch_to_str, md5sum
from catcli.logger import Logger
from catcli.decomp import Decomp
from catcli.version import __version__ as VERSION


class Noder:
    """
    handles node in the catalog tree
    There are 4 types of node:
    * "top" node representing the top node (generic node)
    * "storage" node representing a storage
    * "dir" node representing a directory
    * "file" node representing a file
    """

    TOPNAME = 'top'
    METANAME = 'meta'
    TYPE_TOP = 'top'
    TYPE_FILE = 'file'
    TYPE_DIR = 'dir'
    TYPE_ARC = 'arc'
    TYPE_STORAGE = 'storage'
    TYPE_META = 'meta'
    CSV_HEADER = ('name,type,path,size,indexed_at,'
                  'maccess,md5,nbfiles,free_space,'
                  'total_space,meta')

    def __init__(self, debug=False, sortsize=False, arc=False):
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

    def get_storage_names(self, top):
        """return a list of all storage names"""
        return [x.name for x in list(top.children)]

    def get_storage_node(self, top, name, path=None):
        """
        return the storage node if any
        if path is submitted, it will update the media info
        """
        found = None
        for node in top.children:
            if node.type != self.TYPE_STORAGE:
                continue
            if node.name == name:
                found = node
                break
        if found and path and os.path.exists(path):
            found.free = shutil.disk_usage(path).free
            found.total = shutil.disk_usage(path).total
            found.ts = int(time.time())
        return found

    def get_node(self, top, path, quiet=False):
        """get the node by internal tree path"""
        resolv = anytree.resolver.Resolver('name')
        try:
            bpath = os.path.basename(path)
            return resolv.get(top, bpath)
        except anytree.resolver.ChildResolverError:
            if not quiet:
                Logger.err(f'No node at path \"{bpath}\"')
            return None

    def get_node_if_changed(self, top, path, treepath):
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
            if md5 != node.md5:
                msg = f'\tchange: checksum changed for \"{path}\"'
                self._debug(msg)
                return node, True
        self._debug(f'\tchange: no change for \"{path}\"')
        return node, False

    def _rec_size(self, node, store=True):
        """
        recursively traverse tree and return size
        @store: store the size in the node
        """
        if node.type == self.TYPE_FILE:
            self._debug(f'getting node size for \"{node.name}\"')
            return node.size
        msg = f'getting node size recursively for \"{node.name}\"'
        self._debug(msg)
        size = 0
        for i in node.children:
            if node.type == self.TYPE_DIR:
                size = self._rec_size(i, store=store)
                if store:
                    i.size = size
                size += size
            if node.type == self.TYPE_STORAGE:
                size = self._rec_size(i, store=store)
                if store:
                    i.size = size
                size += size
            else:
                continue
        if store:
            node.size = size
        return size

    def rec_size(self, node):
        """recursively traverse tree and store dir size"""
        return self._rec_size(node, store=True)

    ###############################################################
    # public helpers
    ###############################################################
    def format_storage_attr(self, attr):
        """format the storage attr for saving"""
        if not attr:
            return ''
        if isinstance(attr, list):
            return ', '.join(attr)
        attr = attr.rstrip()
        return attr

    def set_hashing(self, val):
        """hash files when indexing"""
        self.hash = val

    ###############################################################
    # node creationg
    ###############################################################
    def new_top_node(self):
        """create a new top node"""
        return anytree.AnyNode(name=self.TOPNAME, type=self.TYPE_TOP)

    def update_metanode(self, top):
        """create or update meta node information"""
        meta = self._get_meta_node(top)
        epoch = int(time.time())
        if not meta:
            attr = {}
            attr['created'] = epoch
            attr['created_version'] = VERSION
            meta = anytree.AnyNode(name=self.METANAME, type=self.TYPE_META,
                                   attr=attr)
        meta.attr['access'] = epoch
        meta.attr['access_version'] = VERSION
        return meta

    def _get_meta_node(self, top):
        """return the meta node if any"""
        try:
            return next(filter(lambda x: x.type == self.TYPE_META,
                        top.children))
        except StopIteration:
            return None

    def file_node(self, name, path, parent, storagepath):
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
        md5 = None
        if self.hash:
            md5 = self._get_hash(path)
        relpath = os.sep.join([storagepath, name])

        maccess = os.path.getmtime(path)
        node = self._node(name, self.TYPE_FILE, relpath, parent,
                          size=stat.st_size, md5=md5, maccess=maccess)
        if self.arc:
            ext = os.path.splitext(path)[1][1:]
            if ext.lower() in self.decomp.get_formats():
                self._debug(f'{path} is an archive')
                names = self.decomp.get_names(path)
                self.list_to_tree(node, names)
            else:
                self._debug(f'{path} is NOT an archive')
        return node

    def dir_node(self, name, path, parent, storagepath):
        """create a new node representing a directory"""
        path = os.path.abspath(path)
        relpath = os.sep.join([storagepath, name])
        maccess = os.path.getmtime(path)
        return self._node(name, self.TYPE_DIR, relpath,
                          parent, maccess=maccess)

    def clean_not_flagged(self, top):
        """remove any node not flagged and clean flags"""
        cnt = 0
        for node in anytree.PreOrderIter(top):
            if node.type not in [self.TYPE_FILE, self.TYPE_DIR]:
                continue
            if self._clean(node):
                cnt += 1
        return cnt

    def flag(self, node):
        """flag a node"""
        node.flag = True

    def _clean(self, node):
        """remove node if not flagged"""
        if not self._has_attr(node, 'flag') or \
                not node.flag:
            node.parent = None
            return True
        del node.flag
        return False

    def storage_node(self, name, path, parent, attr=None):
        """create a new node representing a storage"""
        path = os.path.abspath(path)
        free = shutil.disk_usage(path).free
        total = shutil.disk_usage(path).total
        epoch = int(time.time())
        return anytree.AnyNode(name=name, type=self.TYPE_STORAGE, free=free,
                               total=total, parent=parent, attr=attr, ts=epoch)

    def archive_node(self, name, path, parent, archive):
        """crete a new node for archive data"""
        return anytree.AnyNode(name=name, type=self.TYPE_ARC, relpath=path,
                               parent=parent, size=0, md5=None,
                               archive=archive)

    def _node(self, name, nodetype, relpath, parent,
              size=None, md5=None, maccess=None):
        """generic node creation"""
        return anytree.AnyNode(name=name, type=nodetype, relpath=relpath,
                               parent=parent, size=size,
                               md5=md5, maccess=maccess)

    ###############################################################
    # printing
    ###############################################################
    def _node_to_csv(self, node, sep=',', raw=False):
        """
        print a node to csv
        @node: the node to consider
        @sep: CSV separator character
        @raw: print raw size rather than human readable
        """
        if not node:
            return
        if node.type == self.TYPE_TOP:
            return

        out = []
        if node.type == self.TYPE_STORAGE:
            # handle storage
            out.append(node.name)   # name
            out.append(node.type)   # type
            out.append('')          # fake full path
            size = self._rec_size(node, store=False)
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
            if node.type == self.TYPE_DIR:
                out.append(str(len(node.children)))  # nbfiles
            else:
                out.append('')  # fake nbfiles
            out.append('')  # fake free_space
            out.append('')  # fake total_space
            out.append('')  # fake meta

        line = sep.join(['"' + o + '"' for o in out])
        if len(line) > 0:
            Logger.out(line)

    def _print_node(self, node, pre='', withpath=False,
                    withdepth=False, withstorage=False,
                    recalcparent=False, raw=False):
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
        if node.type == self.TYPE_TOP:
            # top node
            Logger.out(f'{pre}{node.name}')
        elif node.type == self.TYPE_FILE:
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
            attr = ''
            if node.md5:
                attr = f', md5:{node.md5}'
            size = size_to_str(node.size, raw=raw)
            compl = f'size:{size}{attr}'
            if withstorage:
                content = Logger.bold(storage.name)
                compl += f', storage:{content}'
            Logger.file(pre, name, compl)
        elif node.type == self.TYPE_DIR:
            # node of type directory
            name = node.name
            if withpath:
                if recalcparent:
                    name = os.sep.join([self._get_parents(node.parent), name])
                else:
                    name = node.relpath
            name = name.lstrip(os.sep)
            depth = ''
            if withdepth:
                depth = len(node.children)
            if withstorage:
                storage = self._get_storage(node)
            attr = []
            if node.size:
                attr.append(['totsize', size_to_str(node.size, raw=raw)])
            if withstorage:
                attr.append(['storage', Logger.bold(storage.name)])
            Logger.dir(pre, name, depth=depth, attr=attr)
        elif node.type == self.TYPE_STORAGE:
            # node of type storage
            szfree = size_to_str(node.free, raw=raw)
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
            size = self._rec_size(node, store=False)
            size = size_to_str(size, raw=raw)
            disksize = 'totsize:' + f'{size}'
            # format the output
            name = node.name
            args = [
                'nbfiles:' + f'{nbchildren}',
                disksize,
                f'free:{freepercent}',
                'du:' + f'{szused}/{sztotal}',
                timestamp]
            argsstring = ' | '.join(args)
            Logger.storage(pre,
                           name,
                           argsstring,
                           node.attr)
        elif node.type == self.TYPE_ARC:
            # archive node
            if self.arc:
                Logger.arc(pre, node.name, node.archive)
        else:
            Logger.err(f'bad node encountered: {node}')

    def print_tree(self, top, node,
                   fmt='native',
                   raw=False):
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
                self._print_node(thenode, pre=pre, withdepth=True, raw=raw)
        elif fmt == 'csv':
            # csv output
            self._to_csv(node, with_header=header, raw=raw)
        elif fmt == 'csv-with-header':
            # csv output
            Logger.out(self.CSV_HEADER)
            self._to_csv(node, with_header=header, raw=raw)
        elif fmt.startswith('fzf'):
            # flat
            self._to_fzf(top, node, fmt)

    def _to_csv(self, node, raw=False):
        """print the tree to csv"""
        rend = anytree.RenderTree(node, childiter=self._sort_tree)
        for _, _, item in rend:
            self._node_to_csv(item, raw=raw)

    def _fzf_prompt(self, strings):
        # prompt with fzf
        fzf = FzfPrompt()
        selected = fzf.prompt(strings)
        return selected

    def _to_fzf(self, top, node, fmt):
        """
        print node to fzf
        @top: top node
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
            self.print_tree(top, rend, fmt=subfmt)

    def to_dot(self, node, path='tree.dot'):
        """export to dot for graphing"""
        anytree.exporter.DotExporter(node).to_dotfile(path)
        Logger.info(f'dot file created under \"{path}\"')
        return f'dot {path} -T png -o /tmp/tree.png'

    ###############################################################
    # searching
    ###############################################################
    def find_name(self, top, key,
                  script=False, directory=False,
                  startpath=None, parentfromtree=False,
                  fmt='native', raw=False):
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
        """
        self._debug(f'searching for \"{key}\"')
        if not key:
            # nothing to search for
            return None
        start = top
        if startpath:
            start = self.get_node(top, startpath)
        found = anytree.findall(start, filter_=self._callback_find_name(key))
        nbfound = len(found)
        self._debug(f'found {nbfound} node(s)')

        # compile found nodes
        paths = {}
        nodes = []
        for item in found:
            if item.type == self.TYPE_STORAGE:
                # ignore storage nodes
                continue
            if directory and item.type != self.TYPE_DIR:
                # ignore non directory
                continue
            nodes.append(item)

            if parentfromtree:
                paths[self._get_parents(item)] = item
            else:
                paths[item.relpath] = item

        if fmt == 'native':
            for item in nodes:
                self._print_node(item, withpath=True,
                                 withdepth=True,
                                 withstorage=True,
                                 recalcparent=parentfromtree,
                                 raw=raw)
        elif fmt.startswith('csv'):
            if fmt == 'csv-with-header':
                Logger.out(self.CSV_HEADER)
            for item in nodes:
                self._node_to_csv(item, raw=raw)

        elif fmt.startswith('fzf'):
            selected = self._fzf_prompt(paths)
            newpaths = {}
            subfmt = fmt.replace('fzf-', '')
            for item in selected:
                if item not in paths:
                    continue
                newpaths[item] = paths[item]
                self.print_tree(top, newpaths[item], fmt=subfmt)
            paths = newpaths

        if script:
            tmp = ['${source}/' + x for x in paths]
            tmpstr = ' '.join(tmp)
            cmd = f'op=file; source=/media/mnt; $op {tmpstr}'
            Logger.info(cmd)

        return found

    def _callback_find_name(self, term):
        """callback for finding files"""
        def find_name(node):
            if term.lower() in node.name.lower():
                return True
            return False
        return find_name

    ###############################################################
    # climbing
    ###############################################################
    def walk(self, top, path, rec=False, fmt='native',
             raw=False):
        """
        walk the tree for ls based on names
        @top: start node
        @rec: recursive walk
        @fmt: output format
        @raw: print raw size
        """
        self._debug(f'walking path: \"{path}\"')

        resolv = anytree.resolver.Resolver('name')
        found = []
        try:
            found = resolv.glob(top, path)
            if len(found) < 1:
                # nothing found
                return []

            if rec:
                # print the entire tree
                self.print_tree(top, found[0].parent, fmt=fmt, raw=raw)
                return found

            # sort found nodes
            found = sorted(found, key=self._sort, reverse=self.sortsize)

            # print the parent
            if fmt == 'native':
                self._print_node(found[0].parent,
                                 withpath=False, withdepth=True, raw=raw)
            elif fmt.startswith('csv'):
                self._node_to_csv(found[0].parent, raw=raw)
            elif fmt.startswith('fzf'):
                pass

            # print all found nodes
            if fmt == 'csv-with-header':
                Logger.out(self.CSV_HEADER)
            for item in found:
                if fmt == 'native':
                    self._print_node(item, withpath=False,
                                     pre='- ',
                                     withdepth=True,
                                     raw=raw)
                elif fmt.startswith('csv'):
                    self._node_to_csv(item, raw=raw)
                elif fmt.startswith('fzf'):
                    self._to_fzf(top, item, fmt)

        except anytree.resolver.ChildResolverError:
            pass
        return found

    ###############################################################
    # tree creation
    ###############################################################
    def _add_entry(self, name, top, resolv):
        """add an entry to the tree"""
        entries = name.rstrip(os.sep).split(os.sep)
        if len(entries) == 1:
            self.archive_node(name, name, top, top.name)
            return
        sub = os.sep.join(entries[:-1])
        nodename = entries[-1]
        try:
            parent = resolv.get(top, sub)
            parent = self.archive_node(nodename, name, parent, top.name)
        except anytree.resolver.ChildResolverError:
            self.archive_node(nodename, name, top, top.name)

    def list_to_tree(self, parent, names):
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
    def _sort_tree(self, items):
        """sorting a list of items"""
        return sorted(items, key=self._sort, reverse=self.sortsize)

    def _sort(self, lst):
        """sort a list"""
        if self.sortsize:
            return self._sort_size(lst)
        return self._sort_fs(lst)

    def _sort_fs(self, node):
        """sorting nodes dir first and alpha"""
        return (node.type, node.name.lstrip('.').lower())

    def _sort_size(self, node):
        """sorting nodes by size"""
        try:
            if not node.size:
                return 0
            return node.size
        except AttributeError:
            return 0

    def _get_storage(self, node):
        """recursively traverse up to find storage"""
        if node.type == self.TYPE_STORAGE:
            return node
        return node.ancestors[1]

    def _has_attr(self, node, attr):
        return attr in node.__dict__.keys()

    def _get_parents(self, node):
        """get all parents recursively"""
        if node.type == self.TYPE_STORAGE:
            return ''
        if node.type == self.TYPE_TOP:
            return ''
        parent = self._get_parents(node.parent)
        if parent:
            return os.sep.join([parent, node.name])
        return node.name

    def _get_hash(self, path):
        """return md5 hash of node"""
        return md5sum(path)

    def _debug(self, string):
        """print debug"""
        if not self.debug:
            return
        Logger.debug(string)
