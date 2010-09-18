from svn import fs, core, repos, delta
import string
import time, StringIO, datetime

def split(path):
  return filter(lambda x:x,path.split('/'))
def join(parts):
  return string.join(parts, '/')

svn_node_dir = core.svn_node_dir
svn_node_none = core.svn_node_none
svn_node_file = core.svn_node_file

class RevisionRoot:
  def __init__(self, repository, rev):
    self._repo = repository
    self._rev = rev
    self._root = self._repo._root(self._rev)

    self._last_paths_changed = -1

  def repository(self):
    return self._repo

  def _canonicalize(self, path):
    return self._repo._canonicalize(path)

  def _check(self, cpath):
    return fs.check_path(self._root, cpath)

  def check(self, path):
    return self._check(self._canonicalize(path))

  def rev(self):
    return self._rev

  def created_rev(self, path):
    cpath = self._canonicalize(path)
    return fs.node_created_rev(self._root, cpath)

  def ls(self, path):
    cpath = self._canonicalize(path)
    kind = self._check(cpath)
    if kind != core.svn_node_dir:
      return []
    k = fs.dir_entries(self._root, cpath).keys()
    k.sort()
    return list(k)

  def cat(self, path):
    cpath = self._canonicalize(path)
    kind = self._check(cpath)
    if not kind == core.svn_node_file:
      return None
    
    stream = core.Stream(fs.file_contents(self._root, cpath))
    return stream.read()

  def _history(self,cpath):
    return fs.node_history(self._root,cpath)

  def histories(self,path,cross_copy=False):
    cpath = self._canonicalize(path)
    oh = self._history(cpath)
    while 1:
      oh = fs.history_prev(oh,cross_copy)
      if not oh:
        break
      hpath, hrev = fs.history_location(oh)
      yield hpath,hrev

  def lastmodified_rev(self,path,cross_copy=False):
    cpath = self._canonicalize(path)
    if self.check(cpath) == svn_node_none:
      return '',-1
    oh = self._history(cpath)
    oh = fs.history_prev(oh,cross_copy)
    assert oh
    hpath,hrev = fs.history_location(oh)
    return hpath,hrev

  def previous_rev(self,path,cross_copy=False):
    cpath = self._canonicalize(path)
    if self.check(cpath) == svn_node_none:
      return '',-1
    oh = self._history(cpath)
    oh = fs.history_prev(oh,cross_copy)
    oh = fs.history_prev(oh,cross_copy)
    if not oh:
      return '',-1
    else:
      hpath,hrev = fs.history_location(oh)
      return hpath,hrev

  def path_status(self, path):
    cpath = self._canonicalize(path)
    parts = split(cpath)

    kind = self._check(cpath)

    n = len(parts)
    assert  n>=1

    ret = '''
path: %s
cpath: %s
parts: %s
parts details:
''' % (path,cpath,parts)

    for i in range(len(parts)):
      dpath = join(parts[:i+1])
      kind = self._check(dpath)
      if kind == core.svn_node_dir:
        ret += ' dir  :%s\n'%dpath
      if kind == core.svn_node_none:
        ret += ' none :%s\n'%dpath
      if kind == core.svn_node_file:
        ret += ' file :%s\n'%dpath
    return ret


  def _prop(self,propid):
    ret = fs.revision_prop(self._repo.fs_ptr, self._rev, propid)
    if not ret:
      ret = ''
    return ret

  def author(self):
    return self._prop(core.SVN_PROP_REVISION_AUTHOR)

  def date(self):
    d = self._prop(core.SVN_PROP_REVISION_DATE)
    if d=='':
      return None
    else:
      d = core.svn_time_from_cstring(d)
      return datetime.datetime(*time.gmtime(d / 1000000)[:6])

  def paths_changed(self):
    return fs.paths_changed(self._root)

  def last_paths_changed_rev(self):
    if self._last_paths_changed < 0:
      rev = self.rev()
      while rev>=0:
        for path,sets in fs.paths_changed(self._repo._root(rev)).iteritems():
          if sets.change_kind in [fs.path_change_add, fs.path_change_delete]:
            self._last_paths_changed = rev
            rev = -1
            break
        rev -= 1
    
    return self._last_paths_changed

class Repository:
  def __init__(self, repository_path):
    self.repos_ptr = repos.open(repository_path)
    self.fs_ptr = repos.fs(self.repos_ptr)

  def rev(self):
    return fs.youngest_rev(self.fs_ptr)
  
  def _root(self,rev):
    return fs.revision_root(self.fs_ptr,rev)

  def _canonicalize(self, path):
    return core.svn_path_canonicalize(path)

  def _create_file(self, txn_root, cpath):
    parts = split(cpath)
    dirs = parts[:-1]

    if not self._create_dirs(txn_root, join(dirs)):
      return False
    fs.make_file(txn_root, cpath)
    return True
  
  def _create_dirs(self, txn_root, cpath):
    kind = fs.check_path(txn_root,cpath)
    if kind == core.svn_node_dir:
      return True
    if kind == core.svn_node_file:
      return False
    
    parts = split(cpath)
    if len(parts)<=1:
      return False

    for i in range(len(parts)):
      dpath = join(parts[:i+1])
      kind = fs.check_path(txn_root, dpath)
      if kind == core.svn_node_dir:
        continue
      if kind == core.svn_node_none:
        fs.make_dir(txn_root, dpath)

    return True

  def putfile(self, base_rev, path, inf, uname='', commitmsg='',istext=False):
    cpath = self._canonicalize(path)

    txn = repos.fs_begin_txn_for_commit(self.repos_ptr, base_rev, uname, commitmsg)
    r = None
    try:
      txn_root = fs.txn_root(txn)

      kind = fs.check_path(txn_root, cpath)
      if kind == core.svn_node_none:
        if not self._create_file(txn_root, cpath):
          raise 'svn file creation error: %s'%path
      elif kind == core.svn_node_dir:
        raise 'directory already exists: %s'%cpath
        return None

      if istext:
        fs.change_node_prop(txn_root, cpath, 'svn:eol-style', 'native')

      handler, baton = fs.apply_textdelta(txn_root, cpath, None, None)
      delta.svn_txdelta_send_string(inf.read(), handler, baton)

      r = repos.fs_commit_txn(self.repos_ptr, txn)
    except Exception, a:
      fs.abort_txn(txn)
      raise a

    return r

class RevFile:
  def __init__(self,root,path):
    assert isinstance(root,RevisionRoot)
    assert isinstance(path,str)
    self._path = path
    self._parts = split(path)
    self._root = root
    self._kind = root.check(self._path)

  def parent(self):
    return RevFile(self._root,join(self._parts[:-1]))
                   
  def child(self,child):
    return RevFile(self._root,join(self._parts+[child]))

  def root(self):
    return self._root
  def rev(self):
    return self.root().rev()
  def path(self):
    return self._path

  def ls(self):
    if not self.exist():
      return []
    return self.root().ls(self._path)
  
  def get_data(self):
    assert self.exist()
    return self._root.cat(self._path)
  def history(self):
    for (hpath,hrev) in self._root.histories(self._path):
      yield self._by_rev_path(hrev,hpath)

  def isfile(self):
    return self._kind == svn_node_file
  def isdir(self):
    return self._kind == svn_node_dir
  def exist(self):
    return self._kind != svn_node_none

  def switch_rev(self,rev):
    return self._by_rev_path(rev,self._path)

  def _by_rev_path(self,rev,path):
    r = RevisionRoot(self._root.repository(),rev)
    return RevFile(r,path)

  def changed(self):
    return self.rev()==self.lastmodified_rev()

  def lastmodified_rev(self):
    l = self.lastmodified()
    if l:
      return l.rev()
    else:
      return None
  def previous_rev(self):
    l = self.previous()
    if l:
      return l.rev()
    else:
      return None

  def lastmodified(self):
    p,r = self._root.lastmodified_rev(self._path)
    if r>0:
      return self._by_rev_path(r,p)
    else:
      return None
  def previous(self):
    p,r = self._root.previous_rev(self._path)
    if r>0:
      return self._by_rev_path(r,p)
    else:
      return None

  def basename(self):
    return self._parts[-1]
