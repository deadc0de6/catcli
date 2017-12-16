"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Class that represents a node in the catalog tree
"""

import os
import anytree
import psutil
import time

# local imports
import catcli.utils as utils
from catcli.logger import Logger

'''
There are 4 types of node:
    * "top" node representing the top node (generic node)
    * "storage" node representing a storage
    * "dir" node representing a directory
    * "file" node representing a file
'''


class Noder:

    TOPNAME = 'top'
    TYPE_TOP = 'top'  # tip top ;-)
    TYPE_FILE = 'file'
    TYPE_DIR = 'dir'
    TYPE_STORAGE = 'storage'

    def __init__(self, verbose=False):
        self.hash = True
        self.verbose = verbose

    def set_hashing(self, val):
        self.hash = val

    def get_storage_names(self, top):
        ''' return a list of all storage names '''
        return [x.name for x in list(top.children)]

    def get_node(self, top, path):
        ''' get the node at path '''
        r = anytree.resolver.Resolver('name')
        try:
            return r.get(top, path)
        except anytree.resolver.ChildResolverError:
            Logger.err('No node at path \"{}\"'.format(path))
            return None

    ###############################################################
    # node creationg
    ###############################################################
    def new_top_node(self):
        ''' create a new top node'''
        return anytree.AnyNode(name=self.TOPNAME, type=self.TYPE_TOP)

    def file_node(self, name, path, parent, storagepath):
        ''' create a new node representing a file '''
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
            md5 = utils.md5sum(path)
        relpath = os.path.join(os.path.basename(storagepath),
                               os.path.relpath(path, start=storagepath))
        return self._node(name, self.TYPE_FILE, relpath, parent,
                          size=st.st_size, md5=md5)

    def dir_node(self, name, path, parent, storagepath):
        ''' create a new node representing a directory '''
        path = os.path.abspath(path)
        relpath = os.path.relpath(path, start=storagepath)
        return self._node(name, self.TYPE_DIR, relpath, parent)

    def storage_node(self, name, path, parent, attr=None):
        ''' create a new node representing a storage '''
        path = os.path.abspath(path)
        free = psutil.disk_usage(path).free
        total = psutil.disk_usage(path).total
        epoch = time.time()
        return anytree.AnyNode(name=name, type=self.TYPE_STORAGE, free=free,
                               total=total, parent=parent, attr=attr, ts=epoch)

    def _node(self, name, type, relpath, parent, size=None, md5=None):
        ''' generic node creation '''
        return anytree.AnyNode(name=name, type=type, relpath=relpath,
                               parent=parent, size=size, md5=md5)

    ###############################################################
    # printing
    ###############################################################
    def _print_node(self, node, pre='', withpath=False, withdepth=False):
        ''' print a node '''
        if node.type == self.TYPE_TOP:
            Logger.out('{}{}'.format(pre, node.name))
        elif node.type == self.TYPE_FILE:
            name = node.name
            if withpath:
                name = node.relpath
            attr = ''
            if node.md5:
                attr = ', md5:{}'.format(node.md5)
            compl = 'size:{}{}'.format(utils.human(node.size), attr)
            Logger.file(pre, name, compl)
        elif node.type == self.TYPE_DIR:
            name = node.name
            if withpath:
                name = node.relpath
            depth = ''
            if withdepth:
                depth = len(node.children)
            attr = None
            if node.size:
                attr = [['totsize', utils.human(node.size)]]
            Logger.dir(pre, name, depth=depth, attr=attr)
        elif node.type == self.TYPE_STORAGE:
            hf = utils.human(node.free)
            ht = utils.human(node.total)
            name = '{} (free:{}, total:{})'.format(node.name, hf, ht)
            Logger.storage(pre, name, node.attr)
        else:
            Logger.err('Weird node encountered: {}'.format(node))
            # Logger.out('{}{}'.format(pre, node.name))

    def print_tree(self, node, style=anytree.ContRoundStyle()):
        ''' print the tree similar to unix tool "tree" '''
        rend = anytree.RenderTree(node, childiter=self.sort_tree)
        for pre, fill, node in rend:
            self._print_node(node, pre=pre, withdepth=True)

    ###############################################################
    # searching
    ###############################################################
    def find_name(self, root, key, script=False):
        ''' find files based on their names '''
        if self.verbose:
            Logger.info('searching for \"{}\"'.format(key))
        self.term = key
        found = anytree.findall(root, filter_=self._find_name)
        paths = []
        for f in found:
            if f.type == self.TYPE_STORAGE:
                # ignore storage nodes
                continue
            self._print_node(f, withpath=True, withdepth=True)
            paths.append(f.relpath)
        if script:
            tmp = ['${source}/'+x for x in paths]
            cmd = 'op=file; source=/media/mnt; $op {}'.format(' '.join(tmp))
            Logger.info(cmd)
        return found

    def _find_name(self, node):
        ''' callback for finding files '''
        if self.term.lower() in node.name.lower():
            return True
        return False

    ###############################################################
    # climbing
    ###############################################################
    def walk(self, root, path, rec=False):
        ''' walk the tree for ls based on names '''
        if self.verbose:
            Logger.info('walking path: \"{}\"'.format(path))
        r = anytree.resolver.Resolver('name')
        found = []
        try:
            found = r.glob(root, path)
            if len(found) < 1:
                return []
            if rec:
                self.print_tree(found[0].parent)
                return
            found = sorted(found, key=self.sort_walk)
            self._print_node(found[0].parent,
                             withpath=False, withdepth=True)
            for f in found:
                self._print_node(f, withpath=False, pre='- ', withdepth=True)
        except anytree.resolver.ChildResolverError:
            pass
        return found

    ###############################################################
    # diverse
    ###############################################################
    def sort_tree(self, items):
        ''' sorting a list of items '''
        return sorted(items, key=self.sort_walk)

    def sort_walk(self, n):
        ''' for sorting a node '''
        return (n.type, n.name.lstrip('\.').lower())

    def to_dot(self, node, path='tree.dot'):
        ''' export to dot for graphing '''
        anytree.exporter.DotExporter(node).to_dotfile(path)
        Logger.info('dot file created under \"{}\"'.format(path))
        return 'dot {} -T png -o /tmp/tree.png'.format(path)

    def rec_size(self, node):
        ''' recursively traverse tree and store dir size '''
        if self.verbose:
            Logger.info('getting folder size recursively')
        if node.type == self.TYPE_FILE:
            return node.size
        size = 0
        for i in node.children:
            if node.type == self.TYPE_DIR:
                size += self.rec_size(i)
            if node.type == self.TYPE_STORAGE:
                self.rec_size(i)
            else:
                continue
        node.size = size
        return size
