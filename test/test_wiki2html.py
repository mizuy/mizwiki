# coding:utf-8
from StringIO import StringIO
from mizwiki.wiki2html import *
from nose.tools import *
import re

wiki = u"""
書いた文章とその行間隔は見た目そのまま出力されます。

文章と文章の間に空行を挟むと、それぞれがパラグラフ(p)となります。
空行をはさまずに次の文を書くと、パラグラフ(p)内で改行(br)されます。

チルダを使うと強制的に改行されます。
これはグラフ要素などで使用することを意図しています。~~~~通常の文では使う必要はありません。
"""
result = u"""<p>書いた文章とその行間隔は見た目そのまま出力されます。</p>
<p>文章と文章の間に空行を挟むと、それぞれがパラグラフ(p)となります。
 <br/>
空行をはさまずに次の文を書くと、パラグラフ(p)内で改行(br)されます。</p>
<p>チルダを使うと強制的に改行されます。
 <br/>
これはグラフ要素などで使用することを意図しています。 <br/>
 <br/>
 <br/>
 <br/>
通常の文では使う必要はありません。</p>
"""

def test_wiki2html():
    r = Wiki2Html().parse('')
    eq_(r, '')

    r = Wiki2Html().parse(wiki)
    eq_(r, result)
    
    r = Wiki2Html().parse(wiki.encode('utf-8'))
    eq_(r, result.encode('utf-8'))
    
    
syntax = [('pre',
u"""{{{
hoge
}}}
""",
u"""<pre>
hoge
</pre>
"""),

('pre2', 
u"""{{{#
hoge
}}}
""",
u"""<pre>hoge
</pre>
"""),

('pre-option', 
u"""
{{{#python
def hoge():
    return hoge
}}}
""",
u"""<div class="highlight"><pre><span class="k">def</span> <span class="nf">hoge</span><span class="p">():</span>
    <span class="k">return</span> <span class="n">hoge</span>
</pre></div>
""")

]
def test_syntax():
    for name, src, result in syntax:
        r = Wiki2Html().parse(src)
        eq_(r, result, '%s test failed., src=%s\nexpected=%s\nbut=%s'%(name,src,result,r))
    
