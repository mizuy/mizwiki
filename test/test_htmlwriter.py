# encoding:utf-8
from mizwiki import htmlwriter
from nose.tools import *

from StringIO import StringIO

def test_htmlwriter():
    s = StringIO()
    w = htmlwriter.WikiWriter(s)
    w.push('body')
    w.push('body')
    w.push('a')
    w.pop()
    w.push('body')
    w.insertc('br')
    w.insert('title','title')
    w.pop()
    w.text('hoganona')
    w.text('hdkkaskdfn')
    w.text('hoganona3')
    w.a('hogehoge',href='http://&&Jlkjasdf.lkjalsdf==++||/lsls;&amp;',cls='tt',id='hogehoge',lalal='asdf')
    o = htmlwriter.OUListWriter(w)
    o.move(1)
    w.text('a')
    o.move(2)
    w.text('bbbb1')
    w.text('bbbb2')
    w.text('bbbb3')
    o.move(1)
    w.text('a')
    o.move(1)
    w.text('a')
    o.move(1)
    o.move(2)
    w.text('bbbb1')
    w.text('bbbb2')
    w.text('bbbb3')
    w.text('a')
    o.move(1)
    w.text('a')
    o.finish()
    w.pop()
    w.pop()

    eq_(s.getvalue(), """<body>
 <body>
  <a></a>
  <body>
   <br/>
   <title>title</title>
  </body>
hoganonahdkkaskdfnhoganona3  <a lalal="asdf" href="http://&amp;&amp;Jlkjasdf.lkjalsdf==++||/lsls;&amp;amp;" id="hogehoge" class="tt">hogehoge</a>
  <ul>
   <li>a
    <ul>
     <li>bbbb1bbbb2bbbb3</li>
    </ul>
   </li>
   <li>a</li>
   <li>a</li>
   <li>
    <ul>
     <li>bbbb1bbbb2bbbb3a</li>
    </ul>
   </li>
   <li>a</li>
  </ul>
 </body>
</body>
""")
    

def test_unicode():
    "note: do not use cStringIO.StringIO, which can not handle unicode"
    s = StringIO()
    w = htmlwriter.WikiWriter(s)

    w.push('body')
    w.insert('title',u'タイトル')
    w.pop()

    eq_(s.getvalue(), u"""<body>
 <title>タイトル</title>
</body>
""")
    
