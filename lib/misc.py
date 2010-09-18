# -*- coding:utf-8 mode:Python -*-

import string, os
import popen2 as _popen2, tempfile as _tempfile
import config, re

# igb
re_igbpost = re.compile('&#x([0-9a-f]+);')
def _repl(m):
  return unichr(int(m.group(1),16)).encode('utf-8')

def igb_post_decode(src):
  return re_igbpost.sub(_repl,src)

def file_copy(f,t):
  while True:
    chunk = f.read(1024*1024)
    if not chunk:
      break
    t.write(chunk)

def merge(mydata,olddata,yourdata,label0,label1,label2):
  '''
  merge file with diff3 algorithm
  return code
  0: succeed without conflict
  1: conflict
  2: error
  '''
  p0 = _tempfile.mktemp(dir=config.tmp_dir)
  p1 = _tempfile.mktemp(dir=config.tmp_dir)

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
