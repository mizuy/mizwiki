# -*- coding: utf-8 -*-
import re

class Lexer:
    def __init__(self,source):
        "source's newline must be '\n'. '\r' is regarded as normal charactor"
        self.source = source
        self.len_ = len(self.source)
        self.pos_ = 0
        self.nextl = -1

    def __getitem__(self,i):
        return self.source[i]

    def __len__(self):
        return self.len_

    def get_remainder(self):
        return self[self.pos():]

    def pos(self):
        return self.pos_

    def get_line(self,advance=False):
        if self.nextl < 0:
            t = self.source.find('\n',self.pos_)
            if t<0:
                self.nextl = self.len_
            else:
                self.nextl = t
            
        f = self.pos_
        t = self.nextl
        if advance:
            self.set_pos(t+1)
        return self.source[f:t]

    def set_pos(self,pos):
        self.pos_ = pos
        self.nextl = -1

    def startswith(self,prefix):
        return self.source.startswith(prefix,self.pos_)

    def skipspace(self):
        while not self.eof() and self.source[self.pos_].isspace():
            self.skip(1)

    def skipline(self):
        self.get_line(True)

    def skip(self,num):
        self.set_pos(self.pos_+num)

    def search(self,regex,advance=False):
        m = regex.search(self.source,self.pos_)
        if advance:
            if m:
                self.set_pos(m.end())
            else:
                self.set_pos(self.len_)
        return m

    def eof(self):
        return self.len_ <= self.pos_

class ReLexer:
    def __init__(self,lexer):
        self.stack = None
        self.lexer = lexer

    def __getattr__(self,key):
        return getattr(self.lexer,key)

    def lex(self,regex):
        if self.stack:
            r = self.stack
            self.stack = None
            return r
        else:
            pos = self.pos_
            m = self.search(regex,True)
            if m:
                text = self.lexer[pos:m.start()]
                if text:
                    self.stack = None,m
                else:
                    return None,m
            else:
                text = self.lexer[pos:self.pos_]
            return text,None

    def eof(self):
        return self.lexer.eof() and not self.stack

class WikiParserBase(object):
    def parse(self, source):
        lexer = Lexer(source)
        self.begin_document()
        parse_body(lexer, self, 0)
        return self.end_document()

    def begin_document(self):
        pass
    def end_document(self):
        pass

    ########### Section ###########
    def begin_section(self,sectionn,title_parser,aname,position):
        '''
        sectionn: section deepness
        title_parser(doci):
        aname:
        position:
        '''
        pass
    def end_section(self):
        pass

    ########### Blockquote ###########
    def begin_blockquote(self):
        pass
    def end_blockquote(self):
        pass

    ########### Para ###########
    def begin_para(self):
        pass
    def end_para(self):
        pass

    ########### Pre ###########
    def begin_pre(self):
        pass
    def end_pre(self):
        pass

    ########### Inline Elements ###########
    def br(self):
        pass
    def horizontal_line(self):
        pass
    def text_pre(self,text):
        pass
    def text(self,text):
        pass
    def command(self,cmdname,params):
        pass
    def empathis(self,text):
        pass
    def deleteline(self,text):
        pass
    def underline(self,text):
        pass

    def identity(self,ids):
        pass

    ########### Link ###########
    # label maybe None
    def link_uri(self,label,uri):
        pass
    def link_wiki(self,label,wikiname,wikianame):
        pass
    
    # <a href=uri><img/></a>
    def link_img_uri(self,img_params,uri):
        pass
    def link_img_wiki(self,img_params,wikiname):
        pass

    ########### Foornote ###########
    def begin_footnote(self):
        pass
    def end_footnote(self):
        pass

    ########### List ###########
    def begin_list(self):
        pass
    def end_list(self):
        pass
    def begin_list_element(self,level,ol):
        pass
    def end_list_element(self):
        pass

    ########### Table ###########
    def begin_table(self):
        pass
    def end_table(self):
        pass
    def begin_table_row(self):
        pass
    def end_table_row(self):
        pass
    def begin_table_cell(self,ishead,style_class):
        pass
    def end_table_cell(self):
        pass


class WikiParserDump(WikiParserBase):
    def __init__(self,writer):
        self.w = writer
        
    def begin_document(self):
        self.w.write('<doc>\n')
    def end_document(self):
        self.w.write('</doc>\n')

    ########### Section ###########
    def begin_section(self,sectionn,title_parser,aname,position):
        '''
        sectionn: section deepness
        title_parser(doci):
        aname:
        position:
        '''
        self.w.write('<section num="%s">\n'%sectionn)
        self.w.write('<title>')
        title_parser(DI_dump(self.w))
        self.w.write('</title>')
        
    def end_section(self):
        self.w.write('</section>\n')

    ########### Blockquote ###########
    def begin_blockquote(self):
        self.w.write('<blockquote>\n')
    def end_blockquote(self):
        self.w.write('</blockquote>\n')

    ########### Para ###########
    def begin_para(self):
        self.w.write('<p>\n')
    def end_para(self):
        self.w.write('</p>\n')

    ########### Pre ###########
    def begin_pre(self):
        self.w.write('<pre>\n')
    def end_pre(self):
        self.w.write('</pre>\n')

    ########### Inline Elements ###########
    def br(self):
        self.w.write('<br/>\n')
    def horizontal_line(self):
        self.w.write('<hr/>\n')
    def text_pre(self,text):
        self.w.write(text)
    def text(self,text):
        self.w.write(text)
    def command(self,cmdname,params):
        self.w.write('<command name="%s" params="%s"/>\n')
    def empathis(self,text):
        self.w.write('<empathis>\n')
        self.w.write(text)
        self.w.write('</empathis>\n')
    def deleteline(self,text):
        self.w.write('<deleteline>\n')
        self.w.write(text)
        self.w.write('</deleteline>\n')
    def underline(self,text):
        self.w.write('<underline>\n')
        self.w.write(text)
        self.w.write('</underline>\n')

    def identity(self,ids):
        for i in ids:
            self.w.write('<empathis>\n')
            self.w.write(i)
            self.w.write('</empathis>\n')

    ########### Link ###########
    # label maybe None
    def link_uri(self,label,uri):
        self.w.write('<a href="%s">%s</a>\n'%(uri,label))
    def link_wiki(self,label,wikiname,wikianame):
        self.w.write('<a href="%s">%s</a>\n'%(wikiname+"#"+wikianame,label))
    
    # <a href=uri><img/></a>
    def link_img_uri(self,img_params,uri):
        self.w.write('<a href="%s"><img src="%s"/></a>\n'%(url,img_params))
    def link_img_wiki(self,img_params,wikiname):
        self.w.write('<a href="%s"><img src="%s"/></a>\n'%(wikiname,img_params))

    ########### Foornote ###########
    def begin_footnote(self):
        self.w.write('<foornote>\n')
        pass
    def end_footnote(self):
        self.w.write('</foornote>\n')
        pass

    ########### List ###########
    def begin_list(self):
        self.w.write('<list>\n')
    def end_list(self):
        self.w.write('</list>\n')
        pass
    def begin_list_element(self,level,ol):
        self.w.write('<li lebel="%s">\n'%level)
        pass
    def end_list_element(self):
        self.w.write('</li>\n')

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


re_section = re.compile(r'(.+)\[#([_a-zA-Z0-9]+)\]\s*')
re_cmd0 = re.compile(r'#(\w+):(.*)$')
re_cmd1 = re.compile(r'#(\w+)\(([^)]*)\)$')
re_cmd2 = re.compile(r'#(\w+)$')

def parse_body(lexer,doci,section):
    '''
    parse data from lexer, and interpret and write to doc
    negative section means that context is in footnote instead of section body
    '''
    class qstack:
        def __init__(self,doci):
            self.d = doci
            self.n = 0
        def close(self):
            if self.n>0:
                self.d.end_blockquote()
                self.n -= 1
        def closeall(self):
            while self.n>0:
                self.close()

        def push(self):
            self.closeall()
            self.n+=1
            self.d.begin_blockquote()
            
    class pstack:
        def __init__(self,doci):
            self.d = doci
            self.n = False
        def close(self):
            if self.n:
                self.d.end_para()
            self.n = False
        def push(self):
            self.close()
            assert not self.n
            self.n = True
            self.d.begin_para()
            
        def in_p(self):
            return self.n

    bq = qstack(doci)
    p = pstack(doci)
    def close():
        p.close()
        bq.closeall()
            
    while not lexer.eof():
        if section>=0 and lexer.startswith('*'):
            close()

            l = lexer.get_line()
            inline = l.lstrip('*')
            n = len(l)-len(inline)

            if n>section:
                aname = None
                m = re_section.match(inline)
                if m:
                    inline = m.group(1)
                    aname = m.group(2)

                def title_parser(docit):
                    parse_line(Lexer(inline),docit,False)

                doci.begin_section(n,title_parser,aname,lexer.pos())
                lexer.skipline()
                parse_body(lexer,doci,n)
                doci.end_section()

                continue
            else:
                break

        if lexer.startswith('|'):
            p.close()
            parse_table(lexer,doci)
            continue

        if lexer.startswith('==='):
            l = lexer.get_line()
            if l.strip().replace('=','')=='':
                lexer.skipline()
                p.close()
                doci.horizontal_line()
                continue

        if lexer.startswith('+') or lexer.startswith('-'):
            p.close()
            parse_list(lexer,doci)
            continue

        lexer.skipspace()

        if lexer.startswith('#'):
            l = lexer.get_line()
            m = re_cmd0.match(l.strip())
            if m:
                lexer.skipline()
                p.close()
                doci.command(m.group(1),m.group(2))
                continue

            m = re_cmd1.match(l.strip())
            if m:
                lexer.skipline()
                p.close()
                doci.command(m.group(1),m.group(2))
                continue

            m = re_cmd2.match(l.strip())
            if m:
                lexer.skipline()
                p.close()
                doci.command(m.group(1),'')
                continue

        # ['<<<','>>>','{{{','}}}','/+','))']:

        if lexer.startswith('<<<'):
            lexer.skip(3)
            close()
            bq.push()
            continue

        if lexer.startswith('>>>'):
            lexer.skip(3)
            close()
            continue

        if lexer.startswith('/+'):
            parse_comment(lexer)
            continue

        if lexer.startswith('{{{'):
            p.close()
            parse_pre(lexer,doci)
            continue

        if lexer.startswith('}}}'):
            lexer.skip(3)
            doci.end_pre()
            continue

        # escape footnote
        if lexer.startswith('))'):
            if section < 0:
                close()
                lexer.skip(2)
                break

        l = lexer.get_line()
        if not l or l.isspace():
            p.close()
            lexer.skipline()
            continue

        if p.in_p():
            doci.br()
        else:
            p.push()

        parse_line(lexer,doci,True,section<0)

    p.close()
    bq.closeall()


def parse_list(lexer,doci):
    doci.begin_list()
    while not lexer.eof():
        l = lexer.get_line()
        if l.startswith('+'):
            inline = l.lstrip('+')
            ol = True
        elif l.startswith('-'):
            inline = l.lstrip('-')
            ol = False
        else:
            break

        level = len(l)-len(inline)
        doci.begin_list_element(level,ol)
        lexer.skip(level)
        parse_line(lexer,doci,True)
        doci.end_list_element()
    doci.end_list()



############## Line Parsing #######################

re_cmd_img = re.compile(r'#img\(([^)]*)\)$')

'''
urllabel:  [[(Label:)Link]]
        where Link = URL | WikiName(#aname)

nakedurl:       URL
''empasis''
__underline__
%%delete%%
//comment

/+ /+ nest comment +/ +/
((footnote))
{block}
'''

re_line = re.compile(r'''
\n | ~
| <<< | >>>
| {{{ | }}}
| /\+
| ''(?P<empathis>[^\n]+?)''
| %%(?P<deleteline>[^\n]+?)%%
| __(?P<underline>[^\n]+?)__
| s?https?:\/\/[-_.!~*\'\(\)a-zA-Z0-9;\/?:\@&=+\$,%#]+
| \(\(
| \)\)
| //
| @(?P<identity>[\w\s\-_,]+);
| \[\[
    (?:(?P<label>(?:(?<!\]\]).)+):)??
    (?:
        (?P<url>s?https?:\/\/[-_.!~*\'\(\)a-zA-Z0-9;\/?:\@&=+\$,%#]+?)
      | (?P<wikiname>[\.\w\-+_][\.\w\-+_/\s]*)?(?P<aname>\#[_a-zA-Z0-9]+)?
    )
  \]\]
''',(re.VERBOSE|re.U))

def parse_line(lexer, doci, enable_footnote, within_footnote=False):
    def gg(m,i):
        return m.group(i)
        
    l = ReLexer(lexer)
    while not l.eof():
        text,m = l.lex(re_line)

        if text:
            doci.text(text)
            continue
        elif m:
            pt = m.group(0)
            if pt=='\n':
                break
            elif pt in ['<<<','>>>','{{{','}}}','/+']:
                lexer.skip(-len(pt))
                break
            elif pt=='))':
                if within_footnote:
                    lexer.skip(-len(pt))
                    break
                else:
                    doci.text('))')
                    
            elif pt=='~':
                doci.br()
            elif pt.startswith("''"):
                doci.empathis(gg(m,'empathis'))
            elif pt.startswith("%%"):
                doci.deleteline(gg(m,'deleteline'))
            elif pt.startswith("__"):
                doci.underline(gg(m,'underline'))
            elif pt=='//':
                lexer.skipline()
                break
            elif pt=='((':
                if enable_footnote:
                    doci.begin_footnote()
                    parse_body(lexer,doci,-1)
                    doci.end_footnote()
                    continue
                else:
                    doci.text('((')
            elif pt.startswith('shttp') or pt.startswith('http'):
                doci.link_uri(pt,pt)
            elif pt.startswith('@'):
                i = [s.strip() for s in gg(m,'identity').split(',')]
                doci.identity(i)
            elif pt.startswith('[['):
                label = gg(m,'label')
                url = gg(m,'url')
                wikiname = gg(m,'wikiname')
                if not wikiname:
                    wikiname = '.'
                wikianame = gg(m,'aname')
                if not wikianame:
                    wikianame = ''

                if label:
                    m = re_cmd_img.match(label)
                    if m:
                        params = m.group(1).split(',')
                        if url:
                            doci.link_img_uri(params,url)
                        else:
                            doci.link_img_wiki(params,wikiname)
                    elif url:
                        doci.link_uri(label,url)
                    else:
                        doci.link_wiki(label,wikiname,wikianame)
                else:
                    if url:
                        doci.link_uri(None,url)
                    else:
                        doci.link_wiki(None,wikiname,wikianame)
            else:
                assert not 'unreachable'


re_comment = re.compile(r'//|\+/|/\+')
def parse_comment(lexer):
    assert lexer.startswith('/+')
    commentn = 0
    
    while not lexer.eof():
        m = lexer.search(re_comment,True)
        if not m:
            break
        pt = m.group(0)
        if pt=='//':
            lexer.skipline()
        elif pt=='/+':
            commentn += 1
        elif pt=='+/':
            commentn -= 1
            if commentn<=0:
                return

re_pre = re.compile(r'}}}|\n')
def parse_pre(lexer,doci):
    assert lexer.startswith('{{{')

    lexer.skip(3)
    doci.begin_pre()
    l = ReLexer(lexer)
    
    while not l.eof():
        text,m = l.lex(re_pre)

        if text:
            doci.text_pre(text)
            doci.text_pre('\n')
            continue
        else:
            pt = m.group(0)
            if pt=='\n':
                doci.text('\n')
                continue
            if pt=='}}}':
                break
    doci.end_pre()







############## Table Parsing #######################

def lstrip1(s,m):
    assert s[:len(m)]==m
    return s[len(m):]

re_table_optwidth = re.compile(r'width\s*=\s*(\d+(?:%|px|em)?)$')

class Cell:
    def __init__(self):
        self.calign = ''
        self.cwidth = ''
        self.cth = False
        self.colspan = 1
        self.rowspan = 1
        self.data = ''
        self.skip = False

    def get_class(self):
        cattr = {'class':cls_align[self.calign]}
        if self.colspan>1:
            cattr.update({'colspan':str(self.colspan)})
        if self.rowspan>1:
            cattr.update({'rowspan':str(self.rowspan)})
        if self.cwidth:
            cattr.update({'style':'width:%s'%self.cwidth})
        return cattr

cls_align = {
    'c':'t_center',
    'r':'t_right',
    'l':'t_left',
    '':''
    }

def parse_table(lexer,doci):
    table = []
    modrow = None
    
    num = -1

    activerow = None

    # phase 1. scanning
    while not lexer.eof():
        if not lexer.startswith('|'):
            break
        
        l = lexer.get_line().rstrip()

        mod = ''
        if l.endswith('|'):
            cols = l[1:-1].split('|')
        else:
            v = l[1:].split('|')
            cols = v[:-1]
            mod = (v[-1]).strip()

        if num>=0 and num!=len(cols):
            break

        num = len(cols)

        # ok pop from stream
        lexer.skipline()

        # empty table
        if num==0:
            break

        # initialization at the first row
        if not modrow:
            modrow = [Cell() for i in range(num)]
        if not activerow:
            activerow = [-1 for i in range(num)]

        if mod=='c':
            for i in range(num):
                for c in cols[i].lower().split(','):
                    c = c.strip()
                    if c in 'rcl':
                        modrow[i].calign=c
                    elif c=='th':
                        modrow[i].cth=True
                    elif c.startswith('w'):
                        m=re_table_optwidth.match(c)
                        if m:
                            modrow[i].cwidth = m.group(1)
        else:
            table.append([Cell() for i in range(num)])
            row = table[-1]
            rowi = len(table)-1

            colspanc = 0
            activecol = -1
            for i,c in enumerate(cols):
                
                row[i].calign=modrow[i].calign
                row[i].cwidth=modrow[i].cwidth
                row[i].cth = modrow[i].cth or (mod=='h')
                row[i].data = ''
                
                cs = c.strip()
                if cs=='>':
                    activecol = -1
                    if i+1==num:
                        activecol = i
                        row[i].colspan += colspanc
                        colspanc = 0
                        activerow[i] = rowi
                    else:
                        row[i].skip = True
                        colspanc += 1
                elif cs=='<':
                    if activecol < 0:
                        activecol = i
                        row[i].colspan += colspanc
                        colspanc = 0
                        activerow[i] = rowi
                    else:
                        row[i].skip = True
                        row[activecol].colspan += 1
                elif cs=='^':
                    if activerow[i] < 0:
                        activerow[i] = rowi
                    else:
                        target = table[activerow[i]][i]
                        if target.colspan > 1 or target.skip:
                            activerow[i] = rowi
                        else:
                            target.rowspan += 1
                            row[i].skip = True
                else:
                    activecol = i
                    row[i].colspan += colspanc
                    colspanc = 0
                    activerow[i] = rowi
                    
                    if c.startswith('CENTER:'):
                        c = lstrip1(c,'CENTER:')
                        row[i].calign='c'
                    elif c.startswith('RIGHT:'):
                        c = lstrip1(c,'RIGHT:')
                        row[i].calign='r'
                    elif c.startswith('LEFT:'):
                        c = lstrip1(c,'LEFT:')
                        row[i].calign='l'

                    row[i].data = c

    # phase 2, dump
    doci.begin_table()
    for rowi,r in enumerate(table):
        doci.begin_table_row()
        for c in r:
            if c.skip:
                continue
            doci.begin_table_cell(ishead=c.cth,style_class=c.get_class())
            l = Lexer(c.data)
            parse_line(l,doci,True)
            doci.end_table_cell()
        doci.end_table_row()
    doci.end_table()

############## Test #######################


if __name__=='__main__':
    import sys
    print('test parser.py')
    sin  = sys.stdin.read()
    sout = sys.stdout

    parse(DI_dump(sout),sin)
