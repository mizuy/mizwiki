# -*- coding:utf-8 mode:Python -*-

from svn import fs, core, repos, delta
import string
import time, StringIO, datetime
from misc import memorize
from os import path
import misc

svn_node_dir = core.svn_node_dir
svn_node_none = core.svn_node_none
svn_node_file = core.svn_node_file

path_change = {
    fs.path_change_modify: 'modified',
    fs.path_change_add: 'added',
    fs.path_change_delete: 'deleted',
    fs.path_change_replace: 'replaced',
    fs.path_change_reset: 'reset',
    }

def _c(path):
    return core.svn_path_canonicalize(path.strip('/'))

def _create_file(txn_root, cpath):
    dirpath = path.dirname(cpath)

    if not _create_dirs(txn_root, dirpath):
        return False
    fs.make_file(txn_root, cpath)
    return True
  
def _create_dirs(txn_root, cpath):
    if not cpath:
        return True
    kind = fs.check_path(txn_root,cpath)
    if kind == core.svn_node_dir:
        return True
    elif kind == core.svn_node_file:
        return False

    for dpath,p in misc.iterdir(cpath):
        dpath = _c(dpath)
        kind = fs.check_path(txn_root, dpath)
        if kind == core.svn_node_none:
            fs.make_dir(txn_root, dpath)
            continue
        pass
    return True

class SvnRepository:
    def __init__(self, repository_path):
        self.repos_ptr = repos.open(repository_path)
        self.fs_ptr = repos.fs(self.repos_ptr)

    def __eq__(self, other):
        return other.repos_ptr == self.repos_ptr

    @memorize
    def get_revision(self, revno):
        return SvnRevision(self, revno)
    def get_file(self, revno, filepath):
        return SvnFile(self.get_revision(revno),filepath)

    @property
    def youngest(self):
        "youngest revision of this repository"
        return self.get_revision(fs.youngest_rev(self.fs_ptr))

    def _root(self,revno):
        return fs.revision_root(self.fs_ptr,revno)

    @memorize
    def _last_paths_changed(self, revno):
        "time complexity is O(number of revision), so memorize it to use. see SvnRevision.lat_paths_changed"
        for r in range(revno, 0, -1):
            for rfile,sets in self.get_revision(r).paths_changed:
                if sets.change_kind in [fs.path_change_add, fs.path_change_delete]:
                    return self.get_revision(r)
                pass
            pass
        return None

class SvnRevision:
    def __init__(self, repository, revno):
        self._repo = repository
        self._revno = revno
        self._root = self._repo._root(self._revno)
    def get_file(self, filepath):
        return SvnFile(self, filepath)

    def __repr__(self):
        return 'SvnRevision(revno=%d)'%(self.revno)
    def __eq__(self, other):
        return other._repo == self._repo and other._revno==self._revno

    @property
    def repository(self):
        return self._repo

    @property
    def revno(self):
        return self._revno
        
    def _prop(self,propid):
        return fs.revision_prop(self._repo.fs_ptr, self._revno, propid) or ''

    @property
    def author(self):
        "author of this commit"
        return self._prop(core.SVN_PROP_REVISION_AUTHOR)

    @property
    def date(self):
        "comitted datetime of this revision. utc, microsecond=0"
        d = self._prop(core.SVN_PROP_REVISION_DATE)
        if not d:
            return None
        return datetime.datetime(*time.gmtime(core.svn_time_from_cstring(d) / 1000000)[:6])

    @property
    def paths_changed(self):
        """
        paths_changed information of this revision.
        return the iterator of SvnFile,sets, where set is svn changesets structure.
        etc: sets.change_kind == fs.path_change_add
        """
        for path,sets in fs.paths_changed(self._root).iteritems():
            yield self.get_file(path),sets

    @property
    def last_paths_changed(self):
        "the latest revision where paths_changed(file create, rename, or deletion) occured before self.revno"
        return self._repo._last_paths_changed(self.revno)

class SvnFile:
    def __init__(self, root, path):
        assert isinstance(root,SvnRevision)
        self._path = _c(path)
        self._revision = root
        self._repo = root.repository

    def __repr__(self):
        return 'SvnFile(revno=%d, %s)'%(self.revno,self.path)
    def __eq__(self, other):
        return other._revision==self._revision and other._path==self._path

    @property
    def repository(self):
        return self._repo
    @property
    def revision(self):
        return self._revision
    @property
    def revno(self):
        return self._revision.revno
    @property
    def path(self):
        return self._path
    @property
    def date(self):
        return self._revision.date

    @property
    @memorize
    def kind(self):
        return fs.check_path(self._revision._root, self.path)

    @property
    def isfile(self):
        return self.kind == svn_node_file
    @property
    def isdir(self):
        return self.kind == svn_node_dir
    @property
    def exist(self):
        return self.kind != svn_node_none

    @property
    def children(self):
        if not self.isdir:
            return
        k = fs.dir_entries(self._revision._root, self.path).keys()
        k.sort()

        for i in k:
            yield SvnFile(self._revision, path.normpath(path.join(self.path,i)))

    def ls_all(self):
        def w_node(node, level):
            for c in node.children:
                if c.isdir:
                    w_node(c, level+1)
                elif c.isfile:
                    yield c, level
        for n,l in w_node(self, 0):
            yield n,l

    @property
    def data(self):
        v = self.open()
        return v.read() if v else None

    def open(self):
        if not self.isfile:
            return None
        stream = core.Stream(fs.file_contents(self._revision._root, self.path))
        return stream

    def history(self,cross_copy=False):
        oh = fs.node_history(self._revision._root,self.path)
        while 1:
            oh = fs.history_prev(oh,cross_copy)
            if not oh:
                break
            hpath, hrevno = fs.history_location(oh)
            yield self.repository.get_file(hrevno, hpath)

    @property
    def created(self):
        return self.switch_rev(fs.node_created_rev(self._revision._root, self.path))

    @property
    def lastmodified(self,cross_copy=False):
        if not self.exist:
            return None
        oh = fs.node_history(self._revision._root,self.path)
        oh = fs.history_prev(oh,cross_copy)
        assert oh
        hpath,hrevno = fs.history_location(oh)
        return self.repository.get_file(hrevno,hpath)
    
    @property
    def previous(self,cross_copy=False):
        if not self.exist:
            return None
        oh = fs.node_history(self._revision._root,self.path)
        oh = fs.history_prev(oh,cross_copy)
        oh = fs.history_prev(oh,cross_copy)
        if not oh:
            return None
        else:
            hpath,hrevno = fs.history_location(oh)
            return self.repository.get_file(hrevno,hpath)

    def switch_rev(self,revno):
        return self.repository.get_file(revno,self.path)

    @property
    def changed(self):
        """True if this file changed in this revision."""
        return self.revno==self.lastmodified.revno

    def write(self, data, uname='', commitmsg='',istext=False):
        txn = repos.fs_begin_txn_for_commit(self._repo.repos_ptr, self.revno, uname, commitmsg)
        r = None
        try:
            txn_root = fs.txn_root(txn)

            kind = fs.check_path(txn_root, self.path)

            if kind == core.svn_node_none:
                if not _create_file(txn_root, self.path):
                    raise 'attempt to create file, but file creation error: %s'%path
                pass

            elif kind == core.svn_node_dir:
                raise 'attempt to create file, but directory already exists: %s'%self.path

            if istext:
                fs.change_node_prop(txn_root, self.path, 'svn:eol-style', 'native')
                pass


            handler, baton = fs.apply_textdelta(txn_root, self.path, None, None)
            delta.svn_txdelta_send_string(data, handler, baton)

            r = repos.fs_commit_txn(self._repo.repos_ptr, txn)
        except Exception, a:
            fs.abort_txn(txn)

        return self.switch_rev(r) if r else None

