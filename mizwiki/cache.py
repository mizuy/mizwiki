class Cache(object):
    def has(self,key):
        pass
  
    def get(self,key):
        pass

    def put(self,key,value):
        pass

    def get_cachedata(self, key, lazyeval):
        try:
            v = self.get(key)
        except KeyError:
            v = lazyeval()
            self.put(key,v)
        return v

class CacheMem(Cache):
    def __init__(self):
        self.cachedb = {}
    
    def has(self,key):
        return self.cachedb.has_key(key)
  
    def get(self,key):
        return self.cachedb[key]

    def put(self,key,value):
        self.cachedb[key]=value

import fcntl, os
from urllib import quote

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
        if not self.has(key):
            raise KeyError

        r = ''
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

from mizwiki.local import metadata, session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, String, Boolean, DateTime, Unicode

Base = declarative_base(metadata=metadata)
class CacheEntry(Base):
    query = session.query_property()
    __tablename__ = 'cacheentries'
    key = Column(String, primary_key=True)
    value = Column(Unicode)

    def __repr__(self):
        return '<CacheEntry %s: %s>'%(self.key, self.value)

    def __init__(self, key, value):
        self.key = key
        self.value = value

class CacheSQL(Cache):
    def has(self,key):
        return not not CacheEntry.query.get(key)

    def get(self,key):
        i = CacheEntry.query.get(key)
        if i:
            return i.value
        else:
            raise KeyError

    def put(self,key,value):
        i = CacheEntry.query.get(key)
        if i:
            i.value = value
        else:
            session.add(CacheEntry(key,value))
            session.commit()
