# coding:utf-8
from StringIO import StringIO
from mizwiki.wikiparser import *
from nose.tools import *
import re

def test_lexer():
    source = 'HOGE FOO BAR\n2nd line\n3rd line\n\n'
    for l in [Lexer(source), ReLexer(Lexer(source))]:
        eq_(l[0],source[0])
        eq_(l[20],source[20])
        eq_(len(l),len(source))

        "get_line, pos"
        eq_(l.get_line(),'HOGE FOO BAR')
        eq_(l.get_line(True),'HOGE FOO BAR')
        eq_(l.pos(),13)
        eq_(l.eof(), False)
        eq_(l.get_line(),'2nd line')
        eq_(l.get_line(True),'2nd line')
        eq_(l.eof(), False)
        eq_(l.get_line(True),'3rd line')
        eq_(l.get_line(True),'')
        eq_(l.get_line(True),None)
        eq_(l.eof(), True)
        eq_(l.get_line(True),None)
        eq_(l.eof(), True)

        "set_pos"
        l.set_pos(1)
        eq_(l.get_line(),'OGE FOO BAR')
        eq_(l.get_line(True),'OGE FOO BAR')
        eq_(l.pos(),13)

        "set_pos"
        l.set_pos(0)
        eq_(l.startswith('HOGE'),True)

        "skipline"
        l.skipline()
        eq_(l.startswith('2nd'),True)

        "skip"
        l.set_pos(0)
        l.skip(4)
        eq_(l.startswith(' FOO'),True)

        "skipspace"
        l.skipspace()
        eq_(l.startswith('FOO'),True)
        l.skipspace()
        eq_(l.startswith('FOO'),True)

        "search"
        l.set_pos(0)
        eq_(not not l.search(re.compile('HOGE')), True)
        eq_(not not l.search(re.compile('HOGE-')), False)
        eq_(l.startswith('HOGE'),True)

        eq_(not not l.search(re.compile('HOGE'),True), True)
        eq_(l.startswith(' FOO'),True)

        eq_(not not l.search(re.compile('\s\w+\s'),True), True)
        eq_(l.startswith('BAR'),True)
        eq_(l.eof(),False)
        eq_(not not l.search(re.compile('[\w\s]+'),True), True)
        eq_(l.eof(),True)

def test_lexer_unicode():
    source = u'ほげ HOGE ほんげ\n二行目\n三行目'
    for l in [Lexer(source), ReLexer(Lexer(source))]:
        eq_(l[0],source[0])
        eq_(l[10],source[10])
        eq_(len(l),len(source))

        "get_line, pos"
        eq_(l.get_line(),u'ほげ HOGE ほんげ')
        eq_(l.get_line(True),u'ほげ HOGE ほんげ')
        eq_(l.pos(),12)
        eq_(l.eof(), False)
        eq_(l.get_line(True),u'二行目')
        eq_(l.eof(), False)
        eq_(l.get_line(True),u'三行目')
        eq_(l.eof(), True)

        "set_pos"
        l.set_pos(1)
        eq_(l.get_line(),u'げ HOGE ほんげ')
        eq_(l.get_line(True),u'げ HOGE ほんげ')
        eq_(l.pos(),12)

        "set_pos"
        l.set_pos(0)
        eq_(l.startswith(u'ほげ'),True)

        "skipline"
        l.skipline()
        eq_(l.startswith(u'二行目'),True)

        "skip"
        l.set_pos(0)
        l.skip(2)
        eq_(l.startswith(u' HOGE'),True)

        "skipspace"
        l.skipspace()
        eq_(l.startswith(u'HOGE'),True)
        l.skipspace()
        eq_(l.startswith(u'HOGE'),True)

        "search"
        l.set_pos(0)
        eq_(not not l.search(re.compile(u'ほげ')), True)
        eq_(not not l.search(re.compile(u'ほげ-')), False)
        eq_(l.startswith(u'ほげ'),True)

        eq_(not not l.search(re.compile(u'ほげ'),True), True)
        eq_(l.startswith(u' HOGE'),True)

        eq_(not not l.search(re.compile(r'\s\w+\s',re.U),True), True)
        eq_(l.startswith(u'ほんげ'),True)
        eq_(l.eof(),False)
        eq_(not not l.search(re.compile(r'[\w\s]+',re.U),True), True)
        eq_(l.eof(),True)
              
def test_relexer():
    source = 'HOGE FOO BAR PIYO PICO HOGE   '
    result = source.split(' ')
    l =  ReLexer(Lexer(source))

    count = 0
    while not l.eof():
        text,match = l.lex(re.compile('\w+'))
        if match:
            eq_(text, None)
            eq_(match.group(0), result[count])
            count += 1
        else:
            eq_(text.isspace(),True)
    
wiki_syntax = u"""
*Syntax  [#a25d53115]

Wikiの文法について

#contents

**文と行、改行 [#aa7b9bae1]
{{{
書いた文章とその行間隔は見た目そのまま出力されます。

文章と文章の間に空行を挟むと、それぞれがパラグラフ(p)となります。
空行をはさまずに次の文を書くと、パラグラフ(p)内で改行(br)されます。

チルダを使うと強制的に改行されます。
これはグラフ要素などで使用することを意図しています。~~~~通常の文では使う必要はありません。
}}}
は以下のようになります。
<<<
書いた文章とその行間隔は見た目そのまま出力されます。

文章と文章の間に空行を挟むと、それぞれがパラグラフ(p)となります。
空行をはさまずに次の文を書くと、パラグラフ(p)内で改行(br)されます。

チルダを使うと強制的に改行されます。
これはテーブル要素などで使用することを意図しています。~~~~通常の文では使う必要はありません。
>>>
**章 [#a70c5e7d2]

{{{
*Section 0 [#section_zero]
**Section 1 [#a555b7d39]
***Section 2 [#a4c50e205]
****Section 3 [#a5af97885]
}}}
は

*Section 0 [#section_zero]
**Section 1 [#a555b7d39]
***Section 2 [#a4c50e205]
****Section 3 [#a5af97885]

という段組になります。
段組の階層の数に制限はありませんが、4段くらいまでが自然です。
段組には自動でアンカーが付与されリンク先となることができ、#contents命令によりTable of Contentsを作ることも出来ます。
アンカーのID（[#ahogehoge]の部分）は特に記述しなければ編集時に自動的に付加されます。自分で設定することもできます。

**List [#a1402c184]
{{{
-その1
-その2
-その3
++その3.1
++その3.2
++その3.3
--その3-1
--その3-2
--その3-3
---その3-3-1
---その3-3-2
-その4
}}}
は
<<<
-その1
-その2
-その3
++その3.1
++その3.2
++その3.3
--その3-1
--その3-2
--その3-3
---その3-3-1
---その3-3-2
-その4
>>>
となります。Listの階層に制限はありません。

**Link [#a0899ba85]
URLを除いて、自動でリンクは張られません。
基本的には、
{{{
[[リンク先]]
[[ラベル:リンク先]]
}}}
という文法になります。
''リンク先''としてはURLか、Wikiのページへの絶対リンク、相対リンクとなり、ページ内のアンカーを付加できます。
相対リンクで記述した場合、自動的に適切なラベルで表示されます。

Wikiのページへのリンクと、外部へのリンクは色でも区別されますし、IGBでの挙動も異なります。
（外部リンクは先頭にshellexec:がつけられて、外部ブラウザーで開くようになります。）

Wikiのページへのリンクはさらに、そのページが存在しているかどうかによって色が変わります。（アンカーが存在するかどうかまではチェックしません）

{{{
-[[http://evewiki.info/w/Wiki/Syntax/]]
-[[Syntax:http://evewiki.info/w/Wiki/Syntax/]]
-[[..]]
-[[./Children]]
-[[./Children#num23]]
-[[Turretのガイドはこちら！:Guide/Turret]]
-[[FAQの項目を参照！:Guide/FAQ#ahogehoge]]
-http://evewiki.info/w/Wiki/Syntax/
}}}
は
<<<
-[[http://evewiki.info/w/Wiki/Syntax/]]
-[[Syntax:http://evewiki.info/w/Wiki/Syntax/]]
-[[..]]
-[[./Children]]
-[[./Children#num23]]
-[[Turretのガイドはこちら！:Guide/Turret]]
-[[FAQの項目を参照！:Guide/FAQ#ahogehoge]]
-http://evewiki.info/w/Wiki/Syntax/
>>>
のようになります。

Wikiの項目へのリンクと、URL形式でのリンクは色で識別可能です。

**Table [#a7a02a2cd]

表の要素を ''|'' で区切ると表になります。

{{{
その1:
|b|a|<|<|c|
|^|a|a|a|^|
|^|a|>|>|c|

その2:
|r,th,width=150|c,width=40em|l|c
|Hea~hogeKjlkjdf~hoge?d0|Head1|Head2|h
|Row1|__Column__|Column|
|hoge|''Column''|Column|
|gege|>|Column|
|Piyo|Hoge|Column|
|LEFT:L|CENTER:C|RIGHT:R|
}}}
は
<<<
その1:
|b|a|<|<|c|
|^|a|a|a|^|
|^|a|>|>|c|

その2:
|r,th,width=150|c,width=40em|l|c
|Hea~hogeKjlkjdf~hoge?d0|Head1|Head2|h
|Row1|__Column__|Column|
|hoge|''Column''|Column|
|gege|>|Column|
|Piyo|Hoge|Column|
|LEFT:L|CENTER:C|RIGHT:R|
>>>
となります。

-後ろに''c''のついた行は以降の行の書式を指定します
--複数のオプションを '','' で区切って指定します。
--rで右アライン、lで左アライン、cで中央アライン
--th でその列がヘッダーになります。
--「width=(サイズ)」 で幅を指定します。単位は、%, em, px のいずれか。
-後ろに''h''のついた行はヘッダー行です
-要素の結合
--表の要素が''>''だと、右の要素と結合します
--表の要素が''<''だと、左の要素と結合します
--表の要素が''^''だと、上の要素と結合します
-要素ごとに先頭に''LEFT:''、''RIGHT:''、''CENTER:''があるとtext-alignとして解釈されます。
--Pukiwikiとの互換性のため用意してあります。編集しずらくなるのでできれば''c''行で指定してください。

**引用 [#a18049003]
{{{
<<< と、>>> で囲むとQuoteになります
}}}

<<<
[[don't forget - live dev blog tonight! - may 10 at 20.00 to 21.00 gmt:http://myeve.eve-online.com/news.asp?a=single&nid=1441&tid=1]]
We'd like to remind everyone to join the Live Dev Blog channel tonight at 20.00 GMT, for a nice evening hosted by Gnauton, Abraxas, Ginger and Eris Discordia. They will discuss the Backstory of EVE and answer your questions.

Please head over to this forum thread for more information on how to participate and don't forget to make sure you have EVE Voice active on your account. 
>>>
のようになります。引用の中では他の構文もそのまま解釈されます。


**整形済みテキスト[#a2531fb6e]
''{{{''と''}}}''で囲むと整形済みテキストになります。整形済みテキストのなかでは文法は解釈されません。改行も保存されます。
{{{
Preの例
[[../../FrontPage]]
}}}

**Contents [#ab00a2fbe]
{{{
#contents
}}}
で
#contents
となります

**コメントアウト [#a3b650ad4]
{{{
「//」は行コメントで、これが書かれた後の文がコメントと解釈され無視されます。
「/+ ～ +/」はブロック型のコメントで、間に書いてある文字が無視されます。
ただし、コメントの中でもコメントだけは解釈され、ネストが可能です。
行コメントとブロック型コメントでは前者が優先されます。
}}}

{{{
なんらかの文。//これはコメントです
このWikiはmod_python/+とsubversion+/を使って書かれています。// ほんがー

ほんがー // /+
ここは本文。

ABC /+ ここはコメント。
/+ネストしたコメント。+/ ここもまだコメント。 
+/ ABC
}}}
これは以下のようになります。:
<<<
なんらかの文。//これはコメントです
このWikiはmod_python/+とsubversion+/を使って書かれています。// ほんがー

ほんがー // /+
ここは本文。

ABC /+ ここはコメント。
/+ネストしたコメント。+/ ここもまだコメント。 
+/ ABC
>>>

**Inline [#a7a27360c]
{{{
''強調''、__アンダーライン__、%%打ち消し線%%
}}}
<<<
''強調''、__アンダーライン__、%%打ち消し線%%
>>>
複数行にまたがっては解釈されません。

**水平線 [#a9f9fd468]
''====''で水平線になります

**数式 [#ac9864f26]
{{{
#tex: y=ax^3+bx^2+c
#tex: \frac{dc}{dt}(t)=c_0\tau(1-\frac{c}{c_0})\sqrt{2\frac{c}{c_0}-(\frac{c}{c_0})^2}
}}}
は
<<<
#tex: y=ax^3+bx^2+c
#tex: \frac{dc}{dt}(t)=c_0\tau(1-\frac{c}{c_0})\sqrt{2\frac{c}{c_0}-(\frac{c}{c_0})^2}
>>>
となります

**コメント [#a9922ae1b]
{{{
#comment
}}}
とかくと、以下のようなコメントフォームになります
<<<
#comment
>>>

**画像、ファイルのリンク [#a0e7639ba]
refコマンドでファイルへのリンクをはったり、画像を貼り付けたりできます。
{{{
''通常の画像'':
#ref(evewiki.png)
''回り込みのテスト'':
#ref(galfleet.jpg,float-left,width=300px)
回り込まれたテキスト
左の絵は
-Gallenteの巨大輸送艦 Obelisk （画面中央）
-護衛の戦艦Megathlonが2隻 （左右に1隻づつ）
-駆逐艦Catalyst 3隻 （横長の小さな船）
以上が艦隊を組んでWarpしている様子です。

#clear
クリアされたテキスト

''ファイルのリンク'':
#ref(eveexport2mssql.py.txt)
}}}
で以下のように画像が張られます。
<<<
''通常の画像'':
#ref(evewiki.png)
''回り込みのテスト'':
#ref(galfleet.jpg,float-left,width=300px)
回り込まれたテキスト
左の絵は
-Gallenteの巨大輸送艦 Obelisk （画面中央）
-護衛の戦艦Megathlonが2隻 （左右に1隻づつ）
-駆逐艦Catalyst 3隻 （横長の小さな船）
以上が艦隊を組んでWarpしている様子です。
#clear
クリアされたテキスト

''ファイルのリンク'':
#ref(eveexport2mssql.py.txt)
>>>

-画像を貼り付ける場合のオプション
--''カンマ「,」'' で区切って複数のオプションを指定できます。
--位置のオプション: right, center,left, float-right, float-left
---floatを解除するには、#clear コマンドを利用する。
--縮小のオプション: width=(サイズ)
---使える単位は、%, px, em

**脚注 [#adc96e40b]

{{{
「((」 と 「))」 で囲むと、その位置に脚注が挿入されます。
}}}

取引量と、全製造に使われたミネラルの量の間の単純相関 (simple correlation) は 0.59 です ((訳注: [[相関係数:http://ja.wikipedia.org/wiki/%E7%9B%B8%E9%96%A2%E4%BF%82%E6%95%B0]] ))。さらなる証拠を示すには製造に使われた量と取引された量の間の関係をテストするより洗練された手法を利用できます。その一つが、定常でない(non-stationary)二つの値の調和(integration)を示すことに使える共和分([[co-integration:http://en.wikipedia.org/wiki/Cointegration]])です。

例。((
脚注のなかでは通常の文法がつかえる。''強調''したり、
-リスト
--リスト
を書いたり。脚注のネスト((脚注のネスト))も可能。ただしわかりにくいので推奨しない。
))
"""

wiki = u"""
書いた文章とその行間隔は見た目そのまま出力されます。

文章と文章の間に空行を挟むと、それぞれがパラグラフ(p)となります。
空行をはさまずに次の文を書くと、パラグラフ(p)内で改行(br)されます。

チルダを使うと強制的に改行されます。
これはグラフ要素などで使用することを意図しています。~~~~通常の文では使う必要はありません。
"""
result = u"""<doc>
<p>
書いた文章とその行間隔は見た目そのまま出力されます。</p>
<p>
文章と文章の間に空行を挟むと、それぞれがパラグラフ(p)となります。<br/>
空行をはさまずに次の文を書くと、パラグラフ(p)内で改行(br)されます。</p>
<p>
チルダを使うと強制的に改行されます。<br/>
これはグラフ要素などで使用することを意図しています。<br/>
<br/>
<br/>
<br/>
通常の文では使う必要はありません。</p>
</doc>
"""

def test_wikiparserbase():
    w = WikiParserBase()
    eq_(None, w.parse(''))
    eq_(None, w.parse(u''))
    eq_(None, w.parse(wiki_syntax))
    eq_(None, w.parse(wiki_syntax.encode('utf-8')))

def test_wikiparserdump():
    h = StringIO()
    WikiParserDump(h).parse(wiki)
    eq_(h.getvalue(), result)
    
    h = StringIO()
    WikiParserDump(h).parse(wiki.encode('utf-8'))
    eq_(h.getvalue().decode('utf-8'), result)
    eq_(h.getvalue(), result.encode('utf-8'))
