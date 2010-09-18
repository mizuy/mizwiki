# -*- coding:utf-8 mode:Python -*-

from xml.sax.saxutils import quoteattr,escape
from urllib import quote,unquote
import page
import config
from wpath import Path
from sets import Set

import wikipage
import htmlwriter

content_type = 'text/html;charset=utf-8'
content_type_text = 'text/plain;charset=utf-8'

keywords = 'Medicine, Medical Science, subverison, python'
site_name = 'Medical Science : Student to Student Wiki'
description = 'Medical Science : Student to Student Wiki'
author = 'mizuy, Tohoku University, school of medicine'
copyright = 'Copyright (c) 2009 mizuy. Permission is granted to copy, distribute and/or modify this document under the terms of the GNU Free Documentation License, Version 1.2 or any later version published by the Free Software Foundation; with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.A copy of the license is included in the section entitled "GNU Free Documentation License".'
use_logo = False
use_copyright_footer = True


def get_writer(output):
    return htmlwriter.WikiWriter(output,True)

def xmldec(w):
    w.write('''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
''')
    #<?xml version="1.0" encoding="UTF-8"?>

               
def htmlheader(w,ri,title,nobot=False):
    w.push('head')
    w.insertc('meta',**{'http-equiv':'content-type', 'content':'text/html; charset=UTF-8'})
    w.insertc('link',rel='stylesheet', href=ri.head_link(page.style), type='text/css')
    w.insert('title',text='%s - %s'%(title,site_name))
    w.insertc('meta',**{'http-equiv':'content-language', 'content':'ja'})
    if nobot:
        w.meta('robots','noindex,nofollow')
    w.insertc('link',rel='shortcut icon', href='/favicon.ico', type="image/vnd.microsoft.icon")
    w.meta('description',description)
    w.meta('keywords',keywords)
    w.meta('rating','general')
    w.meta('author',author)
    w.meta('copyright',copyright)
    w.insertc('link',rel='alternate', href=ri.head_link(page.atom), type='application/atom+xml', title='Atom')
    w.pop()

def header(w):
    w.push('div',id='header')
    if use_logo:
        w.push('span',id='logo')
        w.aimg(page.full_url(page.top),page.full_url(page.logo),'Logo',90,64)
        w.pop()
    w.pop()

def footer(w):
    w.push('div',id='footer')
    if use_copyright_footer:
        w.push('p',cls='copyright')
        w.text(copyright)
        w.pop()
    w.push('p',cls='validation')
    w.aimg('http://validator.w3.org/check?uri=referer',page.full_url(page.valid_xhtml),'Valid XHTML 1.0 Strict',88,31)
    def q(v):
        return quote(v).replace('/','%2F')
    w.aimg('http://jigsaw.w3.org/css-validator/validator?uri=%s'%q(page.full_url(page.style)),page.full_url(page.valid_css),'Valid CSS',88,31)
    w.aimg('http://validator.w3.org/feed/check.cgi?url=%s'%q(page.full_url(page.atom)),page.full_url(page.valid_atom),'Valid Atom 1.0',88,31)
    w.pop()
    w.pop()

def menu(w,h):
    ri = h.ri
    w.push('div',id='navigator')

    w.text('[')
    w.a('FrontPage',href=ri.head_link(page.FrontPage))
    w.text('|')
    w.a('RecentChanges',href=ri.head_link(page.RecentChanges))
    w.text(']')
    w.space()

    link = {
        'Head': ri.head_link(ri.wp.path),
        'History':'./?cmd=history',
        'Attach':'./?cmd=attach',
        'Edit':'./?cmd=edit',
        'View':".",
        'Source':"./?cmd=viewsrc",
        'Diff':"./?cmd=diff",
        }

    g = [
        'Head,History,Attach,Edit'.split(','),
        'View,Source,Diff'.split(',')
        ]
    mi = h.menu_items()
    for j in g:
        if Set(j).intersection(mi):
            w.text('[')
            first = 1
            for i in j:
                if i in mi:
                    if not first:
                        w.text('|')
                    first = 0
                    w.a(i,href=link[i])
            w.text(']')
            w.space()
            
    if config.debug:
        w.text('[')
        w.a('Debug',href='./?cmd=debugview')
        w.text(']')
        w.space()
    w.text('[')
    w.a('Wiki',href=ri.head_link(page.Wiki))
    w.text('|')
    w.a('Syntax',href=ri.head_link(page.Syntax))
    w.text(']')

    w.push('form',method='get', action='http://www.google.co.jp/search')
    w.push('div',id='searchbox')
    w.insertc('input',type='text', name='q', size='18', maxlength='255', value='')
    w.insertc('input',type='hidden', name='sitesearch', value=config.hostname)
    w.insertc('input',type='hidden', name='domains', value=config.hostname)
    w.insertc('input',type='hidden', name='ie', value='UTF-8')
    w.insertc('input',type='hidden', name='oe', value='UTF-8')
    w.insertc('input',type='hidden', name='hl', value='ja')
    w.insertc('input',type='submit', name='btnG', value='search')
    w.pop()
    w.pop()
    
    w.pop()

def pathheader(w,ri):
    w.push('div',id='pathinfo')
    for i in range(len(ri.wp.path)):
        w.push('span',cls='pathinfoitem')
        w.a(ri.wp.path[i].basename(),href=ri.local_link(ri.wp.path[:i+1]))
        w.pop()
        w.text('/')
    w.pop()

    
def content(w,ri):
    sb = wikipage.WikiPage(ri.wp.rev(), page.SideBar)
    if sb.exist():
        w.push('table',border='0', id='twocolumn')
        w.push('tr')
        w.push('td', cls='sidebar')
        w.push('div',id='sidebar')
        w.write(sb.get_relative_xhtml(ri,len(ri.wp.path)))
        w.pop()
        w.pop()
        w.push('td', cls='page')
        w.push('div',id='main')
        w.write(ri.wp.get_xhtml(ri))
        w.pop()
        w.pop()
        w.pop()
        w.pop()
    else:
        w.push('div', id='main')
        w.write(ri.wp.get_xhtml(ri))
        w.pop()

def wiki_footer(w,ri):
    attaches, children = ri.wp.get_attaches_and_children_path()
    linkto = ri.wp.get_linkto()
    w.push('div', cls='attaches')
    w.text('attaches:')
    for f in attaches:
        w.push('span', cls='attachfile')
        w.a(f.basename(),href=ri.local_link(f))
        w.pop()
    w.pop()
    w.push('div', cls='children')
    w.text('unlinked children:')
    for f in children:
        if f not in linkto:
            w.push('span', cls='child')
            w.link_wiki(f.basename(),href=ri.local_link(f))
            w.pop()
    w.pop()

def wiki_footer2(w,ri,wp):
    attaches, children = wp.get_attaches_and_children()
    w.push('div', cls='attaches')
    w.text('attaches:')
    for f in attaches:
        w.push('span', cls='attachfile')
        w.a(f.path.basename(),href=ri.rev_link(f))
        w.pop()
    w.pop()
    w.push('div', cls='children')
    w.text('children:')
    for f in children:
        w.push('span', cls='child')
        w.a(f.path.basename(),href=ri.rev_link(f),cls='wiki')
        w.pop()
    w.pop()

def template(w,h,title,nobot,body):
    ri = h.ri
    xmldec(w)
    w.push('html',**{'xmlns':'http://www.w3.org/1999/xhtml', 'xml:lang':'ja'})
    htmlheader(w,ri,title,nobot)
    w.push('body')

    header(w)
    menu(w,h)
    
    w.hr_full()
    w.push('div',id='body')
    body(w)
    w.pop()
    w.hr_full()
    
    footer(w)

    w.pop()
    w.pop()

def locked_body(w,ri):
    pathheader(w,ri)
    w.hr()
    w.text('このページの編集はロックされています。')

def view_body(w,ri):
    pathheader(w,ri)
    w.hr()
    if not ri.headmode:
        lmr = ri.wp.lastmodified().rev()
        w.textl('過去Revision表示モード。この内容は最新ではない可能性があります。')
        w.link_wiki('最新版を見る',ri.head_link(ri.path))
        w.hr()
        navi(w,ri)
        w.hr()
    content(w,ri)
    w.hr()
    wiki_footer(w,ri)

def attach_body(w,ri,message,question):
    pathheader(w,ri)
    w.hr()
    w.push('form',method='post', action='.', enctype='multipart/form-data')
    
    w.push('div')
    w.insertc('input',type='hidden', name='cmd', value='upload')
    w.insertc('input',type='file', size='100', name='file')
    w.pop()
    
    w.insertc('input', type='submit', value='Upload')
    
    w.pop()
    w.insert('p',message)

def uploaded_body(w,ri,success,message):
    pathheader(w,ri)
    w.hr()
    if success:
        w.insert('p','upload成功')
    else:
        w.insert('p','upload失敗')
        w.insert('p',message)
    w.insert('p','Path: %s'%ri.wp.path.displayname())
    w.a('ページへ行く',href='.')

def notfound_body(w,ri):
    pathheader(w,ri)
    w.hr()
    w.insert('p','このRevisionにこのページは存在しません。')
    w.a('現在のページを見にいく or 編集する',href=ri.head_link(ri.wp.path))

def commited_body(w,ri,success,base_rev,commited_rev):
    pathheader(w,ri)
    w.hr()
    if success:
        w.insert('p','commit成功')
        w.insert('p','この状態でリロードすると二重投稿になってしまいます。上のバーか、下のリンクから元のページへ飛んで下さい。')
    else:
        w.insert('p','commit失敗')
    w.push('p')
    w.text('Path: %s'%ri.wp.path.displayname())
    w.br()
    w.text('Base Revision: %s' % base_rev)
    w.br()
    w.text('New Revision: %s' % commited_rev)
    w.pop()
    w.a('ページへ行く',href='.')

def edit_comment_body(w,ri,comment_no,author,comment_text,message,question):
    pathheader(w,ri)
    w.hr()
    w.insert('p','Current Revision: %s' % ri.wp.rev())
    for m in message.splitlines():
        w.text(m)
        w.br()
    w.hr()

    w.push('form',method='post', action='.')
    w.push('div',cls='comment')

    w.insertc('input',type='hidden', name='cmd', value='comment')
    w.insertc('input',type='hidden', name='comment_no', value=comment_no)
    w.textl('Name: ')
    w.insertc('input',type='text', name='author', size='15', value=author)
    w.insert_comment_box('message',comment_text)
    w.insertc('input',type='submit', name='comment', value='Comment')
    w.br()
    w.pop()
    w.pop()
    
def edit_body(w,ri,preview_text,wiki_text,commitmsg_text,message,paraedit,question):
    pathheader(w,ri)
    w.hr()
    w.insert('p','Current Revision: %s' % ri.wp.rev())
    for m in message.splitlines():
        w.text(m)
        w.br()
    w.hr()
    w.push('form',method='post', action='.', cls='editform')
    w.push('div')
    w.insertc('input',type='hidden', name='cmd', value='commit')
    w.insertc('input',type='hidden', name='base_rev', value=ri.wp.rev())
    if paraedit:
        paraedit_from,paraedit_to = paraedit
        w.insertc('input',type='hidden', name='paraedit_from', value=str(paraedit_from))
        w.insertc('input',type='hidden', name='paraedit_to', value=str(paraedit_to))
        
    w.insert('textarea',wiki_text,cls='edit', name='text', cols='70', rows='30')
    w.text('commit message: (備考)')
    w.insert('textarea',commitmsg_text,cls='commitmsg', name='commitmsg', cols='70', rows='30')

    w.push('div',cls='buttons')
    w.insertc('input',type='submit', name='preview', value='Preview')
    w.insertc('input',type='submit', id='okbutton', value='Save')
    w.pop()
    w.pop()
    w.pop()

    w.push('p')
    w.text('Wikiの文法は')
    w.a('Wiki/Syntax',href=ri.head_link(page.Syntax),cls='wiki')
    w.text('を参照してください。')
    w.text('大きな編集をする場合は')
    w.a('Wiki/編集ガイドライン',href=ri.head_link(page.Guideline),cls='wiki')
    w.text('にも目を通して下さい。')
    w.pop()

    if preview_text:
        w.hr()
        w.push('div',id='main')
        w.write(preview_text)
        w.pop()

def navi(w,ri):
    w.link_wiki('通常の表示モードに戻る',ri.head_link(ri.path))
    w.hr()
    
    w.text('他Revisionナビゲーション:')
    
    lw = htmlwriter.ListWriter(w)
    lw.move(1)
    w.text('Head')
    lw.move(2)
    rp = ri.rev_link(ri.wp)
    w.link_wiki('%s'%ri.wp.rev(),href=rp)
    w.text(', ')
    w.a('diff',href=rp+'?cmd=diff')

    lm = ri.wp.lastmodified()
    lw.move(1)
    w.text('Old Modified Revision:')
    w.br()
    for i in range(3):
        if not lm:
            break
        lw.move(2)
        rp = ri.rev_link(lm)
        w.link_wiki('%s'%lm.rev(),href=rp)
        w.text(', ')
        w.a('diff',href=rp+'?cmd=diff')
        lm = lm.previous()
    
    lw.move(1)
    w.text('Old Revisions:')
    w.br()
    rev = ri.wp.rev()
    lw.move(2)
    w.text(str(ri.wp.rev()))
    for i in range(3):
        r = rev-1-i
        rr = ri.wp.switch_rev(r)
        if not rr.exist():
            break
        rp = ri.rev_link(rr)
        lw.move(2)
        w.link_wiki('%s'%r,href=rp)
        w.text(', ')
        w.a('diff',href=rp+'?cmd=diff')

    lw.finish()

def diff_body(w,ri,title,ffrom,fto,linediffs):
    pathheader(w,ri)
    w.hr()
    navi(w,ri)
    w.hr()
    w.push('div',id='main')
    w.push('div',cls='diff_text')
    w.insert('h1',title)
    if fto.changed():
        for tag,l in linediffs:
            if tag=='del':
                w.insert('span',l,cls='diff_del')
                w.br()
            elif tag=='new':
                w.insert('span',l,cls='diff_new')
                w.br()
            else:
                w.insert('span',l,cls='diff_normal')
                w.br()
    else:
        w.text('no change')
    w.pop()
    w.pop()
    w.hr()
    if fto:
        w.text('To:')
        wiki_footer2(w,ri,fto)
    if ffrom:
        w.text('From:')
        wiki_footer2(w,ri,ffrom)
            
def history_body(w,ri,offset):
    pathheader(w,ri)
    w.hr()
    page_size = 25
    w.push('div',id='main')
    w.insert('h1','History of %s'%ri.wp.path.displayname())

    w.push('span')
    w.a('younger',href='./?cmd=history&offset=%s'%max(0,offset-page_size))
    w.text('|')
    w.a('older',href='./?cmd=history&offset=%s'%(offset+page_size))
    w.pop()

    for index, hwp in enumerate(ri.wp.history()):
        if offset < 0:
            break
        if index < offset:
            continue
        if offset + page_size <= index:
            break
    
        hrev = hwp.rev()
        datetxt = hwp.svn_root().date().ctime()
        rp = ri.rev_link(hwp)

        w.push('h2')
        w.a('Revision %s'%hrev,href=rp)
        w.text(', ')
        w.a('diff',href=rp+'?cmd=diff')
        w.text(', '+datetxt)
        w.pop()
        
        if hwp.has_ndiff():
            nd = hwp.get_ndiff()
            if nd:
                format_ndiff(w,nd)
            else:
                w.insert('p','no changes')
    w.pop()

def recent_body(w,ri,offset):
    pathheader(w,ri)
    w.hr()
    page_size = 25
    w.push('div',id='main')
    w.insert('h1','Recent Changes')

    w.push('span')
    w.a('younger',href='./?offset=%s'%max(0,offset-page_size))
    w.text('|')
    w.a('older',href='./?offset=%s'%(offset+page_size))
    w.pop()

    for ind in range(page_size):
        rev = ri.head_rev-ind-offset
        if rev<=0:
            break

        datetxt = wikipage.wsvn.get_root(rev).date().ctime()
        rtitle = 'Revision %s, %s' % (rev,datetxt)
        w.insert('h2',rtitle)
        for i,(path,hwp,kind) in enumerate(wikipage.get_changesets(rev)):
            if hwp:
                fname = hwp.path.displayname()
                qa = ri.rev_link(hwp)
                dl = qa + '?cmd=diff'
                w.push('h3')
                w.text(kind+': ')
                w.a(fname,href=qa)
                w.text(', ')
                w.a('diff',href=dl)
                w.pop()
                if hwp.has_ndiff():
                    nd = hwp.get_ndiff()
                    if nd:
                        format_ndiff(w,nd)
                    else:
                        w.insert('p','no changes')
            else:
                w.push('h3')
                w.text(kind+': ')
                w.text(path)
                w.pop()
    w.pop()

def sitemap_body(w,ri):
    pathheader(w,ri)
    w.hr()
    w.push('div',id='main')
    w.insert('h1','SiteMap')

    rev = ri.svn_head().last_paths_changed_rev()

    rootf = wikipage.wsvn.get_revfile(rev,page.top)

    lw = htmlwriter.ListWriter(w)

    def w_node(node,level):
        for c in node.ls():
            ci = node.child(c)
            path = wikipage.wsvn.get_path(ci)
            if ci.isdir():
                lw.move(level+1)
                w.link_wiki(c,href=ri.head_link(path))
                w_node(ci,level+1)

    w_node(rootf,0)

    w.pop()

def sitemaptxt(w,ri):
    rev = ri.svn_head().last_paths_changed_rev()
    rootf = wikipage.wsvn.get_revfile(rev,page.top)

    def w_node(node,level):
        for c in node.ls():
            ci = node.child(c)
            path = wikipage.wsvn.get_path(ci)
            if ci.isdir():
                w.text(page.full_url(path))
                w.write('\n')
                w_node(ci,level+1)

    w_node(rootf,0)

def atom(w,ri):
    import datetime, md5
    import utils.uuid as uuid
    def getid(s):
        return str(uuid.UUID(bytes=md5.md5(s).digest()))
    page_size = 30

    w.writel('<?xml version="1.0" encoding="utf-8"?>')
    w.push('feed',**{'xmlns':'http://www.w3.org/2005/Atom', 'xml:lang':'ja'})
    w.insert('title',config.hostname)
    w.insert('subtitle',site_name)
    w.insert('id','urn:uuid:'+getid(config.top_url+'rss'))
    w.insert('updated',ri.svn_head().date().isoformat()+'Z')
    w.insertc('link',href=config.top_url)
    w.insertc('link',rel='self', href=page.full_url(page.atom))
    w.push('author')
    w.insert('name',author)
    w.pop()
    for ind in range(page_size):
        rev = ri.head_rev-ind
        if rev <= 0:
            break
        for i,(path,hwp,kind) in enumerate(wikipage.get_changesets(rev)):
            if not hwp:
                continue
            rurl = ri.full_rev_link(hwp)
            title = 'Revision %s: %s: %s' % (rev,kind,hwp.path)
            pdate = hwp.svn_root().date()

            qa = ri.rev_link(hwp)
            w.push('entry')
            w.insert('title',title,type='text')
            w.insert('id','urn:uuid:'+getid(rurl))
            w.insert('updated',pdate.isoformat()+'Z')
            w.insertc('link',href=rurl)

            nd = hwp.get_ndiff()
            if nd:
                w.push('content',type='xhtml')
                w.push('div',xmlns='http://www.w3.org/1999/xhtml')
                format_ndiff(w,nd,True)
                w.pop()
                w.pop()
            w.pop()
    w.pop()

def format_ndiff(w,nd,simple=False):
    w.push('div',cls='ndiff')
    for l in nd.splitlines():
        if simple or len(l)<1:
            w.write(escape(l.rstrip('\r\n'))+'<br/>\n')
            continue

        h = l[0]
        b = l[1:]
        if h=='+':
            w.insert('span',b,cls='diff_new')
            w.br()
        elif h=='-':
            w.insert('span',b,cls='diff_del')
            w.br()
        else:
            w.insert('span',b,cls='diff_normal')
            w.br()
    w.pop()
