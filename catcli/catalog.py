"""
author: deadc0de6 (https://github.com/deadc0de6)
Copyright (c) 2017, deadc0de6

Class that represents the catcli catalog
"""

import os
import pickle
from anytree.exporter import JsonExporter
from anytree.importer import JsonImporter

# local imports
import catcli.utils as utils
from catcli.logger import Logger


class Catalog:

    def __init__(self, path, pickle=False, verbose=False, force=False):
        self.path = path  # catalog path
        self.verbose = verbose  # verbosity
        self.force = force  # force overwrite if exists
        self.metanode = None
        self.pickle = pickle

    def set_metanode(self, metanode):
        '''remove the metanode until tree is re-written'''
        self.metanode = metanode
        self.metanode.parent = None

    def restore(self):
        '''restore the catalog'''
        if not self.path:
            return None
        if not os.path.exists(self.path):
            return None
        if self.pickle:
            return self._restore_pickle()
        return self._restore_json(open(self.path, 'r').read())

    def save(self, node):
        '''save the catalog'''
        if not self.path:
            Logger.err('Path not defined')
            return False
        d = os.path.dirname(self.path)
        if d and not os.path.exists(d):
            os.makedirs(d)
        elif os.path.exists(self.path) and not self.force:
            if not utils.ask('Update catalog \"{}\"'.format(self.path)):
                Logger.info('Catalog not saved')
                return False
        if d and not os.path.exists(d):
            Logger.err('Cannot write to \"{}\"'.format(d))
            return False
        if self.metanode:
            self.metanode.parent = node
        if self.pickle:
            return self._save_pickle(node)
        return self._save_json(node)

    def _save_pickle(self, node):
        '''pickle the catalog'''
        pickle.dump(node, open(self.path, 'wb'))
        if self.verbose:
            Logger.info('Catalog saved to pickle \"{}\"'.format(self.path))
        return True

    def _restore_pickle(self):
        '''restore the pickled tree'''
        root = pickle.load(open(self.path, 'rb'))
        if self.verbose:
            m = 'Catalog imported from pickle \"{}\"'.format(self.path)
            Logger.info(m)
        return root

    def _save_json(self, node):
        '''export the catalog in json'''
        exp = JsonExporter(indent=2, sort_keys=True)
        with open(self.path, 'w') as f:
            exp.write(node, f)
        if self.verbose:
            Logger.info('Catalog saved to json \"{}\"'.format(self.path))
        return True

    def _restore_json(self, string):
        '''restore the tree from json'''
        imp = JsonImporter()
        root = imp.import_(string)
        if self.verbose:
            Logger.info('Catalog imported from json \"{}\"'.format(self.path))
        return root
