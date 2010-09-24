
import misc
from nose.tools import *

def test_relpath():
    eq_(misc.relpath('a/b/c','.'), 'a/b/c')
    eq_(misc.relpath('.','a/b/c'), 'a/b/c')
    eq_(misc.relpath('a/b/file','a/b/d/file'),'../file')
    eq_(misc.relpath('a/b/d/file','a/b/file'),'d/file')

    eq_(misc.relpath('a/file','a/b/c/file'),'../../file')
    eq_(misc.relpath('a/b/file','a/b/c/file'),'../file')
    eq_(misc.relpath('a/b/c/file','a/b/c/file'),'file')

    eq_(misc.relpath('a/b/c/e/file','a/b/c/e/file'),'file')
    eq_(misc.relpath('a/b/c/e/file','a/b/c/file'),'e/file')
    eq_(misc.relpath('a/b/c/e/file','a/b/file'),'c/e/file')
    eq_(misc.relpath('a/b/c/e/file','a/file'),'b/c/e/file')

    eq_(misc.relpath('h/b/c/e/file','a'),'h/b/c/e/file')

def test_iterdir():
    eq_(list(misc.iterdir('')), [])
    eq_(list(misc.iterdir('d')), [('d','d')])
    eq_(list(misc.iterdir('a/b/c/d')), [('a','a'),('a/b','b'),('a/b/c','c'),('a/b/c/d','d')])
