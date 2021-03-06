from mizwiki import svnrep
from cStringIO import StringIO
from nose.tools import *
from datetime import datetime
import os

"""
% svnadmin create 'repo_path'
"""

repo_path = os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__),'testrep')))

def test_repository():
    print repo_path
    repo = svnrep.SvnRepository(repo_path)
    rev0 = repo.youngest
    n = rev0.revno+1
    rf = rev0.get_file('auaua%d/hogehoge_revision%d.txt'%(n,n))

    "adding new file, check last_paths_changed"
    d_before = datetime.utcnow().replace(microsecond=0)

    text = 'Revision No: %03d'%(rev0.revno+1)
    rf1 = rf.write(text, 'testuser', 'test commit')
    rev1 = rf1.revision
    d_after = datetime.utcnow().replace(microsecond=0)

    eq_(rev1.revno, rev0.revno+1)
    eq_(rev1.last_paths_changed.revno, rev1.revno)
    eq_(rev1.author, 'testuser')

    ok_(d_before <= rev1.date <= d_after)


    ok_(rf1.changed)
    ok_(rf1.isfile)
    ok_(not rf1.isdir)
    ok_(rf1.exist)

    eq_(rf1.data, text)
    eq_(rf1.lastmodified, rf1)
    eq_(rf1.previous, None)
    eq_(rf1.created, rf1)

    "modify existing file, check last_paths_changed"
    text = 'Revision No: %03d'%(rev1.revno+1)
    rf2 = rf1.write(text, 'testuser2', 'test commit')
    rev2 = rf2.revision
    eq_(rev2.last_paths_changed.revno, rev1.revno)

    ok_(rf2.changed)
    ok_(rf2.isfile)
    ok_(not rf2.isdir)
    ok_(rf2.exist)

    eq_(rf2.data, text)
    eq_(rf2.lastmodified, rf2)
    eq_(rf2.previous, rf1)
    eq_(rf2.created, rf2)
    

def test_crlf():
    repo = svnrep.SvnRepository(repo_path)
    rev0 = repo.youngest

    "eol-style settings are ignored."
    "eol-style = native"
    rf = rev0.get_file('test_crlf_native.txt')
    rf = rf.write('HOGE\nHOGE', 'testuser', 'test commit', True)
    eq_(rf.data, 'HOGE\nHOGE')
    rf = rf.write('HOGE\r\nHOGE', 'testuser', 'test commit', True)
    eq_(rf.data, 'HOGE\r\nHOGE')

    "eol-style = not native"
    rf = rev0.get_file('test_crlf_not_native.txt')
    rf = rf.write('HOGE\nHOGE', 'testuser', 'test commit', False)
    eq_(rf.data, 'HOGE\nHOGE')
    rf = rf.write('HOGE\r\nHOGE', 'testuser', 'test commit', False)
    eq_(rf.data, 'HOGE\r\nHOGE')
