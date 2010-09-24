# -*- coding: utf-8 -*-

#import io
from cStringIO import StringIO
from urllib import quote,urlencode

import re, string
from os import path

import wikiparser, htmlwriter
import plugin_contents as contents
import config

import md5
#import hashlib

class ConvertInterface(object):
    def page_exist(self,path):
        return False

def trunc_int(minimum,maximum,value):
    assert minimum <= maximum
    return min(max(value,minimum),maximum)

re_paraedit = re.compile(r'@@@paraedit:(\d+)@@@')
class Paraedit:
    '''
    recording starting and ending positions of the sections,
    and insert links for paragraph-editing
    '''
    def __init__(self):
        self.sections = []

    def add_section_paraedit(self, w, deep, position, insert_link=True):
        n = len(self.sections)
        self.sections.append((deep,position))
        if insert_link:
            w.link_edit("@@@paraedit:%s@@@"%n)

    def post_filter(self,src):
        lexer = wikiparser.Lexer(src)
        
        def replace(match):
            f,t = 0,len(lexer)

            n = int(match.group(1))
                
            ndeep,f = self.sections[n]
            for deep,pos in self.sections[n+1:]:
                if deep <= ndeep:
                    t = pos
                    break

            return './?'+urlencode({'cmd':'edit','paraedit_from':str(f),'paraedit_to':str(t)})
        #return './?'+urllib.parse.urlencode({'cmd':'edit','paraedit_from':str(f),'paraedit_to':str(t)})

        return re_paraedit.sub(replace,lexer.source)

    @staticmethod
    def get_paraedit_section(input,paraedit_from,paraedit_to):
        lexer = wikiparser.Lexer(input)
        paraedit_from = trunc_int(0,len(lexer),paraedit_from)
        paraedit_to = trunc_int(paraedit_from,len(lexer),paraedit_to)
        return lexer[paraedit_from:paraedit_to]

    @staticmethod
    def apply_paraedit(input,paraedit_from,paraedit_to,paraedit_body):
        lexer = wikiparser.Lexer(input)
        paraedit_from = trunc_int(0,len(lexer),paraedit_from)
        paraedit_to = trunc_int(paraedit_from,len(lexer),paraedit_to)
        return lexer[0:paraedit_from] + paraedit_body + lexer[paraedit_to:]


class Footnote:
    # self.w: root DocumentWiki
    def __init__(self):
        self.list = []

    # doc: current context
    def get_new_footnote(self, w, fn_content):
        num = len(self.list)+1
        name = '*%s' % num
        aname = 'a_fn_%s' % num

        self.list.append((fn_content,name,aname))

        w.link_footnote('(%s)'%name,href='#'+aname,iden=aname+'_foot')

    def finish(self,w):
        if not len(self.list):
            return
        
        w.push('div',id='footnote')
        for fn_content,name,aname in self.list:
            w.link_wiki(name,href='.#'+aname+'_foot')
            w.anchor('',aname)
            w.write(fn_content.getvalue())
        w.pop()

class Comment:
    def __init__(self):
        self.commentn = 0

    def convert(self,w):
        w.push('form',method="post", action=".")
        w.push('div',cls="comment")

        w.insertc('input',type="hidden", name="cmd", value="comment")
        w.insertc('input',type="hidden", name="comment_no", value=str(self.commentn))
        w.textl('Name: ')
        w.insertc('input',type="text", name="author", size="15")
        w.insert_comment_box('message')
        w.insertc('input',type="submit", name="comment", value="Comment")
        w.pop()
        w.pop()
        self.commentn += 1

    @staticmethod
    def insert_comment(input,os,comment_no,author,message,datetxt):
        def wl(text):
            os.write(text+'\n')

        message = '~'.join(message.splitlines())
        istr = StringIO(input)
        commentn = 0

        for l in istr:
            l = l.rstrip('\n\r')
            if l.strip()=='#comment':
                if commentn==comment_no:
                    if author:
                        wl('-%s -- [[%s:user/%s]] (%s)'%(message,author,author,datetxt))
                    else:
                        wl('-%s -- (%s)'%(message,datetxt))
                commentn += 1
            wl(l)

        if not ( commentn>=comment_no ):
            return False
        return True

re_aname = re.compile(r'\[#([_a-zA-Z0-9]+)\]')

def pre_convert_wiki(indata):
    outf = StringIO()
    def wl(text):
        outf.write(text+'\n')
    istr = StringIO(indata)

    for l in istr:
        l = l.rstrip('\n\r')
        if l.startswith('*'):
            m = re_aname.search(l)
            if m:
                wl(l)
                continue
            else:
                c = md5.new(l).hexdigest()[:8]
                '''
                m = hashlib.md5()
                m.update(l)
                c = m.hexdigest()[:8]
                '''
                wl(l + ' [#a%s]'%c)
                continue
        wl(l)
    return outf.getvalue()

def wiki_to_xhtml(path,ci,source):
    wc = WikiConverter(path,ci)
    wikiparser.parse(wc,source)
    return wc.outputs

re_text = re.compile(r'''
[a-zA-Z0-9_]+
| 。
| 、
| [\s]+
| [\.,\'"\-\+!@#$%\^&*()|\\\[\]{};:<>/?]+
''',re.VERBOSE)

class WikiConverter(wikiparser.DocumentInterface):
    def __init__(self,current_path,ci):
        self.current_path = path.normpath(current_path)
        self.ci = ci

        self.buff = StringIO()
        self.w = htmlwriter.WikiWriter(self.buff)
        self.fn_stack = [self.w]

        self.contents = contents.ContentsTable()
        self.comment = Comment()
        self.footnote = Footnote()
        
        self.dep = []
        self.linkto = set()
        self.paraedit = Paraedit()
        self.lw = None

        self.section_count = 0

    def get_wiki_link(self, path):
        return path.normpath(path.relpath(path, self.current_path))

    def wiki_link(self,label,wikiname,aname=''):
        if label:
            l,path = self._makelabel(wikiname)
            #self.add_linkto(path)
        else:
            label,path = self._makelabel(wikiname)
            #self.add_linkto(path)
            label = label.replace('_',' ')

        url = self.ci.get_wiki_link(path)
        if self.ci.page_exist(path):
            self.w.link_wiki(label,url+aname)
        else:
            self.w.link_wikinotfound(label,url+aname)

    def _makelabel(self,wikiname):
        parts = path.split(wikiname.replace(' ','_'))
        isdir = parts[-1] in ['.','..'] or '.' not in parts[-1]
        path = os.join(parts)

        current = self.ci.get_path()

        if parts[0]=='.':
            name = path.canonicalize().displayname()
            npath = (current + path).canonicalize()
        elif parts[0]=='..':
            name = path.canonicalize().displayname()
            npath = (current + path).canonicalize()
        else:
            name = path.canonicalize().displayname()
            npath = path.canonicalize()

        return name,npath

    def begin_document(self):
        pass
    def end_document(self):
        self.footnote.finish(self.w)
        self.buff = StringIO(self.paraedit.post_filter(self.buff.getvalue()))

        self.contents.finish()
        inputs = self.buff.getvalue()
        
        if self.contents.require_post_conversion:
            tmp = StringIO()
            for l in inputs.splitlines():
                if l.startswith('<#'):
                    if l.strip()==contents.indicator:
                        tmp.write(self.contents.getvalue())
                        tmp.write('\n')
                else:
                    tmp.write(l)
                    tmp.write('\n')
            self.outputs = tmp.getvalue()
        else:
            self.outputs = inputs

    
    ########### Section ###########
    def begin_section(self,sectionn,title_parser,aname,position):
        '''
        sectionn: section deepness
        title_parser(doci):
        aname: can be None
        position:
        '''
        
        self.w.push('h%s'%sectionn)
        title_parser(self)

        self.section_count += 1
        if aname:
            self.w.anchor('_',aname)
        else:
            aname = 'temporal_tag_%s' % self.section_count
            self.w.anchor('',aname)
            
        self.contents.add_section(sectionn,title_parser,aname)

        self.paraedit.add_section_paraedit(self.w,sectionn,position,sectionn<=3)
        self.w.pop()

        self.w.push('div',cls='section%s'%sectionn)
    def end_section(self):
        self.w.pop()

    ########### Blockquote ###########
    def begin_blockquote(self):
        self.w.push('blockquote')
    def end_blockquote(self):
        self.w.pop()

    ########### Para ###########
    def begin_para(self):
        self.w.push('p')
    def end_para(self):
        self.w.pop()

    ########### Pre ###########
    def begin_pre(self):
        self.w.push('pre')
    def end_pre(self):
        self.w.pop()

    ########### Inline Elements ###########
    def br(self):
        self.w.br()
    def horizontal_line(self):
        self.w.hr()

    def text_pre(self,text):
        self.w.text(text)

    def text(self,text):
        text = string.replace(text,'　','  ')
        insert_ws = False
        force_insert_ws = False
            
        r = wikiparser.ReLexer(wikiparser.Lexer(text))
        r.skipspace()
        while not r.eof():
            others,m = r.lex(re_text)

            if others:
                if insert_ws:
                    self.w.text(' ')
                    force_insert_ws = False
                insert_ws = True
                self.w.text(others)
            else:
                assert m
                p = m.group(0)
                if p[0] in ".,'\"-+!@#$%\^&*()|\[]{};:<>/?":
                    if force_insert_ws:
                        self.w.text(' ')
                        force_insert_ws = False
                    self.w.text(p)
                    insert_ws = False
                elif p=='。':
                    self.w.text('. ')
                elif p=='、':
                    self.w.text(', ')
                elif p.isspace():
                    insert_ws = True
                    force_insert_ws = True
                elif p:
                    if insert_ws:
                        self.w.text(' ')
                        force_insert_ws = False
                    self.w.text(p)
                    insert_ws = True

    def command(self,cmdname,params):
        if cmdname=='contents':
            self.contents.convert(self.w)
            return
        elif cmdname=='comment':
            self.comment.convert(self.w)
            return
        elif cmdname=='tex':
            plugin_tex(self.w,params)
            return
        elif cmdname=='ref':
            plugin_ref(self.w,params.split(','))
            return
        elif cmdname=='clear':
            plugin_clear(self.w)
        #elif cmdname=='recent':
        #    recent.convert(self,param.split(','),self.cv,self.ci)
        else:
            self.w.errormsg('no such command: %s'%cmdname)
            return

    def empathis(self,text):
        self.w.empathis(text)
    def deleteline(self,text):
        self.w.deleteline(text)
    def underline(self,text):
        self.w.underline(text)

    def identity(self,ids):
        for i in ids:
            self.w.empathis(i)

    ########### Link ###########
    # label maybe None
    def link_uri(self,label,uri):
        if label:
            self.w.link_external(label,uri)
        else:
            self.w.link_external(uri,uri)
    def link_wiki(self,label,wikiname,wikianame):
        self.wiki_link(label,wikiname,wikianame)
    
    # <a href=uri><img/></a>
    def link_img_uri(self,img_params,uri):
        plugin_img(self.w, img_params, uri)
    def link_img_wiki(self,img_params,wikiname):
        plugin_img(self.w, img_params, wikiname)

    ########### Foornote ###########
    def begin_footnote(self):
        buff = StringIO()
        self.footnote.get_new_footnote(self.w,buff)
        
        self.fn_stack.append(htmlwriter.WikiWriter(buff))
        self.w = self.fn_stack[-1]

    def end_footnote(self):
        self.fn_stack = self.fn_stack[:-1]
        self.w = self.fn_stack[-1]

    ########### List ###########
    def begin_list(self):
        assert not self.lw
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
        self.w.push('table')
    def end_table(self):
        self.w.pop()
    def begin_table_row(self):
        self.w.push('tr')
    def end_table_row(self):
        self.w.pop()
    def begin_table_cell(self,ishead,style_class):
        if ishead:
            self.w.push('th',**style_class)
        else:
            self.w.push('td',**style_class)
    def end_table_cell(self):
        self.w.pop()

############## plugin commands ####################

re_wiki = re.compile(r'([\w_/\.\-]+)')
re_url  = re.compile(r'(s?https?:\/\/[-_.!~*\'\(\)a-zA-Z0-9;\/?:\@&=+\$,%#]+)' )

def is_wikiname(n):
    m = re_wiki.match(n)
    return m!=None
def is_url(n):
    m = re_url.match(n)
    return m!=None


def plugin_tex(w,code):
    qcode = quote('\opaque '+code)
    w.push('div',cls='tex')
    w.img(config.tex_url +'?'+ qcode,code)
    w.pop()

def plugin_clear(w):
    w.push('div',cls='clear')
    w.pop()

def path_filter(f):
    if is_url(f):
        return f
    elif is_wikiname(f):
        return quote(f)
    else:
        return ''

re_ref_optwidth = re.compile(r'\s*width\s*=\s*(\d+(px|em|%))\s*')
def plugin_ref(w, params):
    if len(params)<1:
        w.errormsg('plugin_ref: no parameter given')
        return
    fname = params[0]
    qfname = path_filter(fname)
    if not qfname:
        w.errormsg('plugin_ref: no such file: '+fname)
        return

    w.push('div',cls='reffile')
    w.a('[File] '+fname,href=qfname,cls='reffile')
    w.pop()

def plugin_img(w, params, link_url=None):
    if len(params)<1:
        w.errormsg('plugin_img: no parameter given')
        return

    fname = params[0]
    qfname = path_filter(fname)
    if not qfname:
        w.errormsg('plugin_img: no such file: '+fname)
        return

    roo,ext = os.path.splitext(fname)
    ext = ext.lower()
    isimage = False
    if ext in config.mime_map:
        isimage = config.mime_map[ext].find('image')>=0
    if not isimage:
        w.errormsg('plugin_img: not a image file type: '+fname)
        return

    position = ''
    width = ''
    for p in params[1:]:
        if p in ['center','right','left','float-right','float-left']:
            position = p
        else:
            m = re_ref_optwidth.match(p)
            if m:
                width = m.group(1)
                
    w.push('div',cls='refimage %s'%position)
    if link_url:
        w.push('a',href=link_url)
        if width:
            w.img(fname,fname,width=width)
        else:
            w.img(fname,fname)
        w.pop()
    else:
        if width:
            w.push('a',href=qfname)
            w.img(fname,fname,width=width)
            w.pop()
        else:
            w.img(fname,fname)
    w.pop()

    return


if __name__=='__main__':
    import sys
    print(wiki_to_xhtml(ConvertInterface(),sys.stdin.read()))

