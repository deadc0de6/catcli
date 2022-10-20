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
from catcli.utils import ask
from catcli.logger import Logger


class Catalog:
    """the catalog"""

    def __init__(self, path, usepickle=False, debug=False, force=False):
        """
        @path: catalog path
        @usepickle: use pickle
        @debug: debug mode
        @force: force overwrite if exists
        """
        self.path = path
        self.debug = debug
        self.force = force
        self.metanode = None
        self.pickle = usepickle

    def set_metanode(self, metanode):
        """remove the metanode until tree is re-written"""
        self.metanode = metanode
        self.metanode.parent = None

    def restore(self):
        """restore the catalog"""
        if not self.path:
            return None
        if not os.path.exists(self.path):
            return None
        if self.pickle:
            return self._restore_pickle()
        with open(self.path, 'r', encoding='UTF-8') as file:
            content = file.read()
        return self._restore_json(content)

    def save(self, node):
        """save the catalog"""
        if not self.path:
            Logger.err('Path not defined')
            return False
        directory = os.path.dirname(self.path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        elif os.path.exists(self.path) and not self.force:
            if not ask(f'Update catalog \"{self.path}\"'):
                Logger.info('Catalog not saved')
                return False
        if directory and not os.path.exists(directory):
            Logger.err(f'Cannot write to \"{directory}\"')
            return False
        if self.metanode:
            self.metanode.parent = node
        if self.pickle:
            return self._save_pickle(node)
        return self._save_json(node)

    def _debug(self, text):
        if not self.debug:
            return
        Logger.debug(text)

    def _save_pickle(self, node):
        """pickle the catalog"""
        with open(self.path, 'wb') as file:
            pickle.dump(node, file)
        self._debug(f'Catalog saved to pickle \"{self.path}\"')
        return True

    def _restore_pickle(self):
        """restore the pickled tree"""
        with open(self.path, 'rb') as file:
            root = pickle.load(file)
        msg = f'Catalog imported from pickle \"{self.path}\"'
        self._debug(msg)
        return root

    def _save_json(self, node):
        """export the catalog in json"""
        exp = JsonExporter(indent=2, sort_keys=True)
        with open(self.path, 'w', encoding='UTF-8') as file:
            exp.write(node, file)
        self._debug(f'Catalog saved to json \"{self.path}\"')
        return True

    def _restore_json(self, string):
        """restore the tree from json"""
        imp = JsonImporter()
        root = imp.import_(string)
        self._debug(f'Catalog imported from json \"{self.path}\"')
        return root
