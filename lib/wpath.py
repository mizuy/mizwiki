# -*- coding:utf-8 mode:Python -*-

import string

def split(path):
    return filter(lambda x:x,path.strip('/').split('/'))

def join(parts,isdir=True):
    if isdir:
        return string.join(parts, '/')+'/'
    else:
        return string.join(parts, '/')

def canonicalize(path):
    if not path or path=='/':
        return ''
    return join(split(path),path[-1]=='/')

class Path(object):
    @staticmethod
    def by_parts(parts,isdir=True):
        return Path(join(parts,isdir))

    @staticmethod
    def dotdot(num):
        return Path.by_parts(['..']*num,True)
        
    def __init__(self,path=''):
        self.path_ = canonicalize(path)
        self.parts_ = split(self.path_)
        self.isdir_ = (not self.path_) or self.path_[-1]=='/'
        
    def tofile(self):
        return Path.by_parts(self.parts_,False)
    def todir(self):
        return Path.by_parts(self.parts_,True)
        
    def __add__(self,other):
        if isinstance(other,str):
            other = Path(other)
        dp = self.dirpath()
        return Path.by_parts(dp.parts() + other.parts(),other.isdir())

    def __hash__(self):
        return hash(self.path_)

    def __eq__(self,other):
        return self.path_ == other.path_

    def __str__(self):
        return self.path()
    __repr__ = __str__

    def __len__(self):
        return len(self.parts_)

    def __getitem__(self,i):
        pi = self.parts_[i]
        if isinstance(i,slice):
            if i.stop==len(self) or i.stop is None:
                return Path.by_parts(pi,self.isdir())
            else:
                return Path.by_parts(pi,True)
        else:
            if i==len(self)-1:
                return Path.by_parts([pi],self.isdir())
            else:
                return Path.by_parts([pi],True)

    def isdir(self):
        return self.isdir_
    def isfile(self):
        return not self.isdir_

    def path(self):
        return self.path_
    def parts(self):
        return self.parts_

    def dirpath(self):
        if self.isdir():
            return self
        else:
            return self.parent()

    def parent(self):
        if len(self)>0:
            return Path.by_parts(self.parts_[:-1],True)
        else:
            return Path()

    def filename(self):
        assert not self.isdir()
        return self.parts_[-1]

    def basename(self):
        if len(self)>0:
            return self.parts_[-1]
        else:
            return ''

    def displayname(self):
        return string.join(self.parts(), '/')
        return join(self.parts(),False)

    def canonicalize(self):
        ret = []
        for p in self.parts():
            if p=='.':
                pass
            elif p == '..':
                if len(ret)>0:
                    ret.pop(-1)
            else:
                ret.append(p)
        return Path.by_parts(ret,self.isdir_)
