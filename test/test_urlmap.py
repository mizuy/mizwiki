from mizwiki import urlmap
from nose.tools import *

def test_urlmap():
    def newcont(name):
        def controller(ri, rev=None,path=None):
            return name,rev,path
        return controller

    mapper = urlmap.UrlMap()
    mapper.add_rule('recentchanges', newcont('rc'), '^RecentChanges$')
    mapper.add_rule('atom', newcont('atom'), '^RecentChanges/atom.xml$')

    mapper.add_rule('frontpage', newcont('frontpage'), r'$', 'FrontPage')

    mapper.add_rule('wiki_rev', newcont('wiki_rev'),
                    r'^r(\d+)/([\w_/+\-]+)$', "r%d/%s",["rev","path"])
    mapper.add_rule('wiki_head', newcont('wiki_head'),
                    r'^([\w_/+\-]+)$', "%s", ["path"])

    mapper.add_rule('attach_rev', newcont('attach_rev'),
                    r'^r(\d+)/([\w_./+\-]+)$', "r%d/%s", ["rev","path"])
    mapper.add_rule('attach', newcont('attach'),
                    r'^([\w_/+\-]+\.[\w_]+)$', "%s",["path"])

    eq_(mapper.dispatch('RecentChanges'), ('rc',None,None))
    eq_(mapper.dispatch('RecentChanges/atom.xml'), ('atom',None,None))
    eq_(mapper.dispatch('hogehoge/hogehoge'), ('wiki_head',None,'hogehoge/hogehoge'))
    eq_(mapper.dispatch('hogeko.jpg'), ('attach',None,'hogeko.jpg'))

    eq_(mapper.dispatch('r10/hogehoge/hogehoge'), ('wiki_rev','10','hogehoge/hogehoge'))
    eq_(mapper.dispatch('r10/hogeko.jpg'), ('attach_rev','10','hogeko.jpg'))

    eq_(mapper.dispatch(''), ('frontpage',None,None))

    eq_(mapper.url_for('recentchanges'), 'RecentChanges')
    eq_(mapper.url_for('atom'), 'RecentChanges/atom.xml')
    eq_(mapper.url_for('wiki_head',path='hogehoge/h'), 'hogehoge/h')
    eq_(mapper.url_for('wiki_rev',rev=100,path='hogehoge/h'), 'r100/hogehoge/h')
    eq_(mapper.url_for('attach_rev',rev=45,path='hoge.jpg'), 'r45/hoge.jpg')
    eq_(mapper.url_for('attach',path='hoge.jpg'), 'hoge.jpg')

    eq_(mapper.url_for('frontpage'), 'FrontPage')
