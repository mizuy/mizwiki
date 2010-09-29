from nose.tools import *
from mizwiki.application import application
from BeautifulSoup import BeautifulSoup
from werkzeug import Client, BaseResponse
from werkzeug import EnvironBuilder

def setup():
    pass
def teardown():
    pass


def geth(path):
    c = Client(application, BaseResponse)
    r = c.get(path)
    h = BeautifulSoup(r.data)
    return r.status_code, r.headers, h

def has(a,b):
    ok_(a.find(b)>=0, 'not "%s".find("%s")>=0'%(a,b))

def test_files():
    titles = [
        ('FrontPage.wiki', 'FrontPage.wiki'),
        ('RecentChanges', 'RecentChanges'),
        ('sitemap', 'Sitemap'),
        ('FrontPage.wiki?cmd=edit', 'Edit: FrontPage.wiki'),
        ('FrontPage.wiki?cmd=attach', 'Upload File: FrontPage.wiki'),
        ('FrontPage.wiki?cmd=history', 'History: FrontPage.wiki'),
        ('FrontPage.wiki?cmd=diff', 'Diff: FrontPage.wiki'),
        ('r30/FrontPage.wiki', 'Old File: r30/FrontPage.wiki'),
        ]
    for path, t in titles:
        s, head, h = geth(path)
        eq_(s, 200, path)
        has(h.find('title',).contents[0],t)
