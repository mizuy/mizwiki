import fcntl, os
from urllib import quote

class Cache(object):
  def has(self,key):
    pass
  
  def get(self,key):
    pass

  def put(self,key,value):
    pass

  def get_cachedata(self, key, lazyeval):
    if not self.has(key):
      self.put(key,lazyeval())
    return self.get(key)

class CacheMem(Cache):
  def __init__(self):
    self.cachedb = {}
    
  def has(self,key):
    return self.cachedb.has_key(key)
  
  def get(self,key):
    return self.cachedb[key]

  def put(self,key,value):
    self.cachedb[key]=value


def escapep(v):
  return quote(v).replace('/','%2F')

class CacheFile(Cache):
  def __init__(self,cachedir):
    self.dir_ = cachedir
  
  def has(self,key):
    k = self.dir_ + escapep(key)
    return os.path.exists(k)
  
  def get(self,key):
    k = self.dir_ + escapep(key)
    r = None
    f = open(k,'rb')
    try:
      fcntl.flock(f.fileno(), fcntl.LOCK_SH)
      try:
        r = f.read()
      finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    finally:
      f.close()
        
    return r

  def put(self,key,value):
    k = self.dir_ + escapep(key)
    f = open(k,'wb')
    try:
      fcntl.flock(f.fileno(), fcntl.LOCK_EX)
      try:
        f.write(str(value))
      finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    finally:
      f.close()

from sqlobject import *

class CacheEntry(SQLObject):
  key = StringCol(unique=True)
  value = StringCol()

CacheEntry.createTable(ifNotExists=True)

def get_one(q):
  if q.count():
    return q[0]
  else:
    return None

class CacheSQL(Cache):
  def __init__(self):
    pass
  def has(self,key):
    v = CacheEntry.select(CacheEntry.q.key==key)
    if v.count():
      return True
    return False

  def get(self,key):
    v = CacheEntry.select(CacheEntry.q.key==key)
    i = get_one(v)
    if i:
      return i.value
    return None

  def put(self,key,value):
    v = CacheEntry.select(CacheEntry.q.key==key)
    i = get_one(v)
    if i:
      i.value = value
    else:
      CacheEntry(key=key,value=value)
  
