# -*- mode:python coding: utf-8 -*-

from StringIO import StringIO
from urllib import quote,urlencode
from xml.sax.saxutils import escape

import re, string
import md5
import os
from mizwiki import wikiparser, htmlwriter

class Wiki2Wordpress(wikiparser.WikiParserBase):
    def __init__(self):
        self.buff = StringIO()
        self.w = htmlwriter.WikiWriter(self.buff)
        self.lw = None
        
    def begin_document(self):
        pass
    def end_document(self):
        return self.buff.getvalue()

    ########### Section ###########
    def begin_section(self,sectionn,title_parser,aname,position):
        '''
        sectionn: section deepness
        title_parser(doci):
        aname:
        position:
        '''
        self.w.write('\n\n<strong>')
        title_parser((self))
        self.w.write('</strong>\n')
        
    def end_section(self):
        pass

    ########### Blockquote ###########
    def begin_blockquote(self):
        self.w.write('\n<blockquote>')
    def end_blockquote(self):
        self.w.write('</blockquote>\n')

    ########### Para ###########
    def begin_para(self):
        self.w.write('')
        pass
    def end_para(self):
        self.w.write('')

    ########### Pre ###########
    def begin_pre(self):
        self.w.write('\n<pre lang="python">')
    def end_pre(self):
        self.w.write('</pre>\n')

    ########### Inline Elements ###########
    def br(self):
        self.w.write('\n')
    def horizontal_line(self):
        self.w.write('<hr/>')
    def text_pre(self,text):
        self.w.write(text)
    def text(self,text):
        self.w.write(text)
    def command(self,cmdname,params):
        pass

    def empathis(self,text):
        self.w.write('<strong>')
        self.w.write(text)
        self.w.write('</strong>')
    def deleteline(self,text):
        self.w.write('<deleteline>')
        self.w.write(text)
        self.w.write('</deleteline>')
    def underline(self,text):
        self.w.write('<underline>')
        self.w.write(text)
        self.w.write('</underline>')

    def identity(self,ids):
        for i in ids:
            self.w.write('<empathis>\n')
            self.w.write(i)
            self.w.write('</empathis>\n')

    ########### Link ###########
    # label maybe None
    def link_uri(self,label,uri):
        self.w.write('<a href="%s">%s</a>'%(uri,label))
    def link_wiki(self,label,wikiname,wikianame):
        self.w.write('%s (missing link to %s%s)'%(label,wikiname,wikianame))

    # <a href=uri><img/></a>
    def link_img_uri(self,img_params,uri):
        self.w.write('<a href="%s"><img src="%s"/></a>\n'%(url,img_params))
    def link_img_wiki(self,img_params,wikiname):
        self.w.write('<img src="%s"/>\n'%(img_params))

    ########### Foornote ###########
    def begin_footnote(self):
        self.w.write('((')
        pass
    def end_footnote(self):
        self.w.write('))')
        pass

    ########### List ###########
    def begin_list(self):
        self.lw = htmlwriter.OUListWriter(self.w)
    def end_list(self):
        assert self.lw
        self.lw.finish()
        self.lw = None
    def begin_list_element(self,level,ol):
        assert self.lw
        self.lw.move(level,ol)
    def end_list_element(self):
        pass

    ########### Table ###########
    def begin_table(self):
        self.w.write('<table>\n')
    def end_table(self):
        self.w.write('</table>\n')
    def begin_table_row(self):
        self.w.write('<tr>\n')
    def end_table_row(self):
        self.w.write('</tr>\n')
    def begin_table_cell(self,ishead,style_class):
        self.w.write('<td class="%s">\n'%style_class)
    def end_table_cell(self):
        self.w.write('</td>\n')
