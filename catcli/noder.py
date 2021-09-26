"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Class that represents a node in the catalog tree
"""

import os
import anytree
import shutil
import time

# local imports
from . import __version__ as VERSION
import catcli.utils as utils
from catcli.logger import Logger
from catcli.decomp import Decomp

'''
There are 4 types of node:
    * "top" node representing the top node (generic node)
    * "storage" node representing a storage
    * "dir" node representing a directory
    * "file" node representing a file
'''


class Noder:

    TOPNAME = 'top'
    METANAME = 'meta'
    TYPE_TOP = 'top'
    TYPE_FILE = 'file'
    TYPE_DIR = 'dir'
    TYPE_ARC = 'arc'
    TYPE_STORAGE = 'storage'
    TYPE_META = 'meta'

    def __init__(self, debug=False, sortsize=False, arc=False):
        '''
        @debug: debug mode
        @sortsize: sort nodes by size
        @arch: handle archive
        '''
        self.hash = True
        self.debug = debug
        self.sortsize = sortsize
        self.arc = arc
        if self.arc:
            self.decomp = Decomp()

    def get_storage_names(self, top):
        '''return a list of all storage names'''
        return [x.name for x in list(top.children)]

    def get_storage_node(self, top, name):
        '''return the storage node if any'''
        for n in top.children:
            if n.type != self.TYPE_STORAGE:
                continue
            if n.name == name:
                return n
        return None

    def get_node(self, top, path, quiet=False):
        '''get the node by internal tree path'''
        r = anytree.resolver.Resolver('name')
        try:
            p = os.path.basename(path)
            return r.get(top, p)
        except anytree.resolver.ChildResolverError:
            if not quiet:
                Logger.err('No node at path \"{}\"'.format(p))
            return None

    def get_node_if_changed(self, top, path, treepath):
        '''
        return the node (if any) and if it has changed
        @top: top node (storage)
        @path: abs path to file
        @treepath: rel path from indexed directory
        '''
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
            self._debug('\tchange: maccess changed for \"{}\"'.format(path))
            return node, True
        # test hash
        if self.hash and node.md5:
            md5 = self._get_hash(path)
            if md5 != node.md5:
                m = '\tchange: checksum changed for \"{}\"'.format(path)
                self._debug(m)
                return node, True
        self._debug('\tchange: no change for \"{}\"'.format(path))
        return node, False

    def _rec_size(self, node, store=True):
        '''
        recursively traverse tree and return size
        @store: store the size in the node
        '''
        if node.type == self.TYPE_FILE:
            self._debug('getting node size for \"{}\"'.format(node.name))
            return node.size
        m = 'getting node size recursively for \"{}\"'.format(node.name)
        self._debug(m)
        size = 0
        for i in node.children:
            if node.type == self.TYPE_DIR:
                sz = self._rec_size(i, store=store)
                if store:
                    i.size = sz
                size += sz
            if node.type == self.TYPE_STORAGE:
                sz = self._rec_size(i, store=store)
                if store:
                    i.size = sz
                size += sz
            else:
                continue
        if store:
            node.size = size
        return size

    def rec_size(self, node):
        '''recursively traverse tree and store dir size'''
        return self._rec_size(node, store=True)

    ###############################################################
    # public helpers
    ###############################################################
    def format_storage_attr(self, attr):
        '''format the storage attr for saving'''
        if not attr:
            return ''
        if type(attr) is list:
            return ', '.join(attr)
        attr = attr.rstrip()
        return attr

    def set_hashing(self, val):
        '''hash files when indexing'''
        self.hash = val

    ###############################################################
    # node creationg
    ###############################################################
    def new_top_node(self):
        '''create a new top node'''
        return anytree.AnyNode(name=self.TOPNAME, type=self.TYPE_TOP)

    def update_metanode(self, top):
        '''create or update meta node information'''
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
        '''return the meta node if any'''
        try:
            return next(filter(lambda x: x.type == self.TYPE_META,
                        top.children))
        except StopIteration:
            return None

    def file_node(self, name, path, parent, storagepath):
        '''create a new node representing a file'''
        if not os.path.exists(path):
            Logger.err('File \"{}\" does not exist'.format(path))
            return None
        path = os.path.abspath(path)
        try:
            st = os.lstat(path)
        except OSError as e:
            Logger.err('OSError: {}'.format(e))
            return None
        md5 = None
        if self.hash:
            md5 = self._get_hash(path)
        relpath = os.sep.join([storagepath, name])

        maccess = os.path.getmtime(path)
        n = self._node(name, self.TYPE_FILE, relpath, parent,
                       size=st.st_size, md5=md5, maccess=maccess)
        if self.arc:
            ext = os.path.splitext(path)[1][1:]
            if ext.lower() in self.decomp.get_formats():
                self._debug('{} is an archive'.format(path))
                names = self.decomp.get_names(path)
                self.list_to_tree(n, names)
            else:
                self._debug('{} is NOT an archive'.format(path))
        return n

    def dir_node(self, name, path, parent, storagepath):
        '''create a new node representing a directory'''
        path = os.path.abspath(path)
        relpath = os.sep.join([storagepath, name])
        maccess = os.path.getmtime(path)
        return self._node(name, self.TYPE_DIR, relpath,
                          parent, maccess=maccess)

    def clean_not_flagged(self, top):
        '''remove any node not flagged and clean flags'''
        cnt = 0
        for node in anytree.PreOrderIter(top):
            if node.type != self.TYPE_FILE and node.type != self.TYPE_DIR:
                continue
            if self._clean(node):
                cnt += 1
        return cnt

    def flag(self, node):
        '''flag a node'''
        node.flag = True

    def _clean(self, node):
        '''remove node if not flagged'''
        if not self._has_attr(node, 'flag') or \
                not node.flag:
            node.parent = None
            return True
        del node.flag
        return False

    def storage_node(self, name, path, parent, attr=None):
        '''create a new node representing a storage'''
        path = os.path.abspath(path)
        free = shutil.disk_usage(path).free
        total = shutil.disk_usage(path).total
        epoch = int(time.time())
        return anytree.AnyNode(name=name, type=self.TYPE_STORAGE, free=free,
                               total=total, parent=parent, attr=attr, ts=epoch)

    def archive_node(self, name, path, parent, archive):
        '''crete a new node for archive data'''
        return anytree.AnyNode(name=name, type=self.TYPE_ARC, relpath=path,
                               parent=parent, size=0, md5=None,
                               archive=archive)

    def _node(self, name, type, relpath, parent,
              size=None, md5=None, maccess=None):
        '''generic node creation'''
        return anytree.AnyNode(name=name, type=type, relpath=relpath,
                               parent=parent, size=size,
                               md5=md5, maccess=maccess)

    ###############################################################
    # printing
    ###############################################################
    def _print_node(self, node, pre='', withpath=False,
                    withdepth=False, withstorage=False,
                    recalcparent=False):
        '''
        print a node
        @node: the node to print
        @pre: string to print before node
        @withpath: print the node path
        @withdepth: print the node depth info
        @withstorage: print the node storage it belongs to
        @recalcparent: get relpath from tree instead of relpath field
        '''
        if node.type == self.TYPE_TOP:
            # top node
            Logger.out('{}{}'.format(pre, node.name))
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
                attr = ', md5:{}'.format(node.md5)
            compl = 'size:{}{}'.format(utils.human(node.size), attr)
            if withstorage:
                compl += ', storage:{}'.format(Logger.bold(storage.name))
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
                attr.append(['totsize', utils.human(node.size)])
            if withstorage:
                attr.append(['storage', Logger.bold(storage.name)])
            Logger.dir(pre, name, depth=depth, attr=attr)
        elif node.type == self.TYPE_STORAGE:
            # node of type storage
            hf = utils.human(node.free)
            ht = utils.human(node.total)
            nbchildren = len(node.children)
            freepercent = '{:.1f}%'.format(
                node.free * 100 / node.total
            ).ljust(6)
            # get the date
            dt = ''
            if self._has_attr(node, 'ts'):
                dt = 'date: '
                dt += '{}'.format(utils.epoch_to_str(node.ts)).ljust(11)
            ds = ''
            # the children size
            sz = self._rec_size(node, store=False)
            sz = utils.human(sz)
            ds = 'totsize:' + '{}'.format(sz).ljust(7)
            # format the output
            name = '{}'.format(node.name)
            args = [
                'nbfiles:' + '{}'.format(nbchildren).ljust(6),
                ds,
                'free:{}'.format(freepercent),
                'du:' + '{}/{}'.format(hf, ht).ljust(14),
                dt]
            Logger.storage(pre,
                           name.ljust(20),
                           '{}'.format(','.join(args)),
                           node.attr)
        elif node.type == self.TYPE_ARC:
            # archive node
            if self.arc:
                Logger.arc(pre, node.name, node.archive)
        else:
            Logger.err('bad node encountered: {}'.format(node))

    def print_tree(self, node, style=anytree.ContRoundStyle()):
        '''print the tree similar to unix tool "tree"'''
        rend = anytree.RenderTree(node, childiter=self._sort_tree)
        for pre, fill, node in rend:
            self._print_node(node, pre=pre, withdepth=True)

    def to_dot(self, node, path='tree.dot'):
        '''export to dot for graphing'''
        anytree.exporter.DotExporter(node).to_dotfile(path)
        Logger.info('dot file created under \"{}\"'.format(path))
        return 'dot {} -T png -o /tmp/tree.png'.format(path)

    ###############################################################
    # searching
    ###############################################################
    def find_name(self, root, key,
                  script=False, directory=False,
                  startpath=None, parentfromtree=False):
        '''find files based on their names'''
        self._debug('searching for \"{}\"'.format(key))
        start = root
        if startpath:
            start = self.get_node(root, startpath)
        self.term = key
        found = anytree.findall(start, filter_=self._find_name)
        paths = []
        for f in found:
            if f.type == self.TYPE_STORAGE:
                # ignore storage nodes
                continue
            if directory and f.type != self.TYPE_DIR:
                # ignore non directory
                continue
            self._print_node(f, withpath=True, withdepth=True,
                             withstorage=True, recalcparent=parentfromtree)
            if parentfromtree:
                paths.append(self._get_parents(f))
            else:
                paths.append(f.relpath)
        if script:
            tmp = ['${source}/' + x for x in paths]
            cmd = 'op=file; source=/media/mnt; $op {}'.format(' '.join(tmp))
            Logger.info(cmd)
        return found

    def _find_name(self, node):
        '''callback for finding files'''
        if self.term.lower() in node.name.lower():
            return True
        return False

    ###############################################################
    # climbing
    ###############################################################
    def walk(self, root, path, rec=False):
        '''walk the tree for ls based on names'''
        self._debug('walking path: \"{}\"'.format(path))
        r = anytree.resolver.Resolver('name')
        found = []
        try:
            found = r.glob(root, path)
            if len(found) < 1:
                return []
            if rec:
                self.print_tree(found[0].parent)
                return found
            found = sorted(found, key=self._sort, reverse=self.sortsize)
            self._print_node(found[0].parent,
                             withpath=False, withdepth=True)
            for f in found:
                self._print_node(f, withpath=False, pre='- ', withdepth=True)
        except anytree.resolver.ChildResolverError:
            pass
        return found

    ###############################################################
    # tree creation
    ###############################################################
    def _add_entry(self, name, top, resolv):
        '''add an entry to the tree'''
        entries = name.rstrip(os.sep).split(os.sep)
        if len(entries) == 1:
            self.archive_node(name, name, top, top.name)
            return
        sub = os.sep.join(entries[:-1])
        f = entries[-1]
        try:
            parent = resolv.get(top, sub)
            parent = self.archive_node(f, name, parent, top.name)
        except anytree.resolver.ChildResolverError:
            self.archive_node(f, name, top, top.name)

    def list_to_tree(self, parent, names):
        '''convert list of files to a tree'''
        if not names:
            return
        r = anytree.resolver.Resolver('name')
        for name in names:
            name = name.rstrip(os.sep)
            self._add_entry(name, parent, r)

    ###############################################################
    # diverse
    ###############################################################
    def _sort_tree(self, items):
        '''sorting a list of items'''
        return sorted(items, key=self._sort, reverse=self.sortsize)

    def _sort(self, x):
        '''sort a list'''
        if self.sortsize:
            return self._sort_size(x)
        return self._sort_fs(x)

    def _sort_fs(self, n):
        '''sorting nodes dir first and alpha'''
        return (n.type, n.name.lstrip('\.').lower())

    def _sort_size(self, n):
        '''sorting nodes by size'''
        try:
            if not n.size:
                return 0
            return n.size
        except AttributeError:
            return 0

    def _get_storage(self, node):
        '''recursively traverse up to find storage'''
        return node.ancestors[1]

    def _has_attr(self, node, attr):
        return attr in node.__dict__.keys()

    def _get_parents(self, node):
        '''get all parents recursively'''
        if node.type == self.TYPE_STORAGE:
            return ''
        parent = self._get_parents(node.parent)
        if parent:
            return os.sep.join([parent, node.name])
        return node.name

    def _get_hash(self, path):
        """return md5 hash of node"""
        return utils.md5sum(path)

    def _debug(self, string):
        '''print debug'''
        if not self.debug:
            return
        Logger.debug(string)
