# -*- coding:utf-8 mode:Python -*-

import string, os, re, difflib, itertools
import popen2 as _popen2, tempfile as _tempfile
from os import path

from mizwiki import config

def relpath(to, start):
    s = path.normpath(start).strip('/').split('/')
    t = path.normpath(to).strip('/').split('/')
    
    if s==['.']:
        return to
    if t==['.']:
        return start
    if s==t:
        return t[-1]

    common = len(list(itertools.takewhile(lambda (a,b):a==b, zip(s,t))))
    back = len(s)-common-1
    d = ['..']*back if back>0 else []
    
    return '/'.join(d+t[common:])

def iterdir(dirpath):
    parts = [x for x in dirpath.strip('/').split('/') if x]
    for index,p in enumerate(parts):
        yield '/'.join(parts[:index+1]), p

def file_copy(f,t):
  while True:
    chunk = f.read(1024*1024)
    if not chunk:
      break
    t.write(chunk)

def read_fs_file(f,maxsize):
    temp = StringIO.StringIO()
    size = 0
    while True:
        size += 1024
        if size>maxsize:
            return None
        chunk = f.read(1024)
        if not chunk:
            break
        temp.write(chunk)
    return temp

def linediff(fromlines,tolines):
  f = fromlines
  t = tolines
  m = difflib.SequenceMatcher(None, fromlines, tolines)

  for tag, i1, i2, j1, j2 in m.get_opcodes():
    fs = f[i1:i2]
    ts = t[j1:j2]
    if tag=='equal':
      for l in fs:
        yield '',l
    elif tag=='replace':
      for l in fs:
        yield 'del',l
      for l in ts:
          yield 'new',l
    elif tag=='insert':
      for l in ts:
        yield 'new',l
    elif tag=='delete':
      for l in fs:
        yield 'del',l
    else:
      raise 'unreachale'

def merge(mydata,olddata,yourdata,label0,label1,label2):
  '''
  merge file with diff3 algorithm
  return code
  0: succeed without conflict
  1: conflict
  2: error
  '''
  p0 = _tempfile.mktemp(dir=config.TMP_DIR)
  p1 = _tempfile.mktemp(dir=config.TMP_DIR)

  ret = ''
  rcode = -1

  try:
    f0 = os.fdopen(os.open(p0,os.O_RDWR|os.O_EXCL|os.O_CREAT),'w+b')
    f1 = os.fdopen(os.open(p1,os.O_RDWR|os.O_EXCL|os.O_CREAT),'w+b')
    f0.write(mydata)
    f1.write(olddata)
    f0.close()
    f1.close()

    p = _popen2.Popen3('diff3 -L "%s" -L "%s" -L "%s" -m -E %s %s -'%(label0,label1,label2,p0,p1))
    p.tochild.write(yourdata)
    p.tochild.close()
    ret = p.fromchild.read()
    p.fromchild.close()

    rcode = p.wait()/256
  finally:
    os.unlink(p0)
    os.unlink(p1)

  return rcode,ret

def _mkdir(newdir):
  """works the way a good mkdir should :)
  - already exists, silently complete
  - regular file in the way, raise an exception
  - parent directory(ies) does not exist, make them as well
  """
  if os.path.isdir(newdir):
    pass
  elif os.path.isfile(newdir):
    raise OSError("a file with the same name as the desired " \
                  "dir, '%s', already exists." % newdir)
  else:
    head, tail = os.path.split(newdir)
    if head and not os.path.isdir(head):
      _mkdir(head)
      #print "_mkdir %s" % repr(newdir)
    if tail:
      os.mkdir(newdir)

# http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
import functools

class memorize(object):
   """Decorator that caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned, and
   not re-evaluated.
   """
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      try:
         return self.cache[args]
      except KeyError:
         value = self.func(*args)
         self.cache[args] = value
         return value
      except TypeError:
         # uncachable -- for instance, passing a list as an argument.
         # Better to not cache than to blow up entirely.
         return self.func(*args)
   def __repr__(self):
      """Return the function's docstring."""
      return self.func.__doc__
   def __get__(self, obj, objtype):
      """Support instance methods."""
      return functools.partial(self.__call__, obj)

def curry(func):
    def inner(*args,**kw):
        def inner2(w):
            func(w,*args,**kw)
        return inner2
    return inner

def curry2(func):
    def inner(*args,**kw):
        def inner2(w,ri):
            func(w,ri,*args,**kw)
        return inner2
    return inner

