# -*- coding:utf-8 mode:Python -*-

from xml.sax.saxutils import escape
from urllib import quote
import page
import config
from sets import Set

from htmlwriter import ListWriter
from misc import curry,curry2
from os import path
import misc
import models

content_type = 'text/html;charset=utf-8'
content_type_text = 'text/plain;charset=utf-8'

def xmldec(w):
    w.write('''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
''')

def htmlheader(w,h,title,nobot=False):
    ri = h.ri
    w.push('head')
    w.insertc('meta',**{'http-equiv':'content-type', 'content':'text/html; charset=UTF-8'})
    w.insertc('link',rel='stylesheet', href=ri.link('theme',path='style.css'), type='text/css')
    w.insert('title',text='%s - %s'%(title,config.SITE_NAME))
    w.insertc('meta',**{'http-equiv':'content-language', 'content':'ja'})
    if nobot:
        w.meta('robots','noindex,nofollow')
    w.insertc('link',rel='shortcut icon', href='/favicon.ico', type="image/vnd.microsoft.icon")
    w.meta('description',config.DESCRIPTION)
    w.meta('keywords',config.KEYWORDS)
    w.meta('rating','general')
    w.meta('author',config.AUTHOR)
    w.insertc('link',rel='alternate', href=ri.link('atom'), type='application/atom+xml', title='Atom')
    w.pop()

def header(w,h):
    ri = h.ri
    w.push('div',id='header')
    if config.LOGO:
        w.push('span',id='logo')
        w.aimg(ri.full_link('wiki_head',path='FrontPage.wiki'),ri.full_link('theme',path=config.LOGO),'Logo',90,64)
        w.pop()
    w.pop()

def footer(w,h):
    ri = h.ri
    w.push('div',id='footer')
    if config.USE_COPYRIGHT_FOOTER:
        w.push('p',cls='copyright')
        w.text('Copyright (c) 2010 tmedic.org Permission is granted to copy, distribute and/or modify this document under the terms of the GNU Free Documentation License, Version 1.2 or any later version published by the Free Software Foundation; with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts.A copy of the license is included in the section entitled ')
        w.a("GNU Free Documentation License",href=ri.link('wiki_head',path='GNU_Free_Documentation_License.wiki'))
        w.text('.')
        w.pop()
    w.push('p',cls='validation')
    w.aimg('http://validator.w3.org/check?uri=referer',
           ri.full_link('theme',path='valid-xhtml10.png'),'Valid XHTML 1.0 Strict',88,31)
    def q(v):
        return quote(v).replace('/','%2F')
    w.aimg('http://jigsaw.w3.org/css-validator/validator?uri=%s'%q(ri.full_link('theme',path='style.css')),
           ri.full_link('theme',path='valid-css.png'),'Valid CSS',88,31)
    w.aimg('http://validator.w3.org/feed/check.cgi?url=%s'%q(ri.full_link('atom')),
           ri.full_link('theme',path='valid-atom.png'),'Valid Atom 1.0',88,31)
    w.pop()
    w.pop()

def menu(w,h):
    ri = h.ri
    w.push('div',id='navigator')

    w.text('[')
    w.a('FrontPage',href=ri.link('frontpage'))
    w.text('|')
    w.a('Sitemap',href=ri.link('sitemap'))
    w.text('|')
    w.a('RecentChanges',href=ri.link('recentchanges'))
    w.text(']')
    w.space()

    g = [
        'Head,History,Attach,Edit'.split(','),
        'View,Source,Diff'.split(',')
        ]
    mi = h.menu_items
    for j in g:
        if Set(j).intersection(mi):
            w.text('[')
            first = 1
            for i in j:
                if i in mi:
                    if not first:
                        w.text('|')
                    first = 0
                    w.a(i,href=h.menu_links[i])
            w.text(']')
            w.space()
            
    w.text('[')
    w.a('Wiki',href=ri.link('wiki_head',path='AboutWiki.wiki'))
    w.text('|')
    w.a('Syntax',href=ri.link('wiki_head',path='Syntax.wiki'))
    w.text(']')

    w.push('form',method='get', action='http://www.google.co.jp/search')
    w.push('div',id='searchbox')
    w.insertc('input',type='text', name='q', size='18', maxlength='255', value='')
    w.insertc('input',type='hidden', name='sitesearch', value=h.ri.hostname)
    w.insertc('input',type='hidden', name='domains', value=h.ri.hostname)
    w.insertc('input',type='hidden', name='ie', value='UTF-8')
    w.insertc('input',type='hidden', name='oe', value='UTF-8')
    w.insertc('input',type='hidden', name='hl', value='ja')
    w.insertc('input',type='submit', name='btnG', value='search')
    w.pop()
    w.pop()
    
    w.pop()

def pathheader(w,h):
    ri = h.ri
    w.push('div',id='pathinfo')
    for path,p in misc.iterdir(ri.path_info):
        w.push('span',cls='pathinfoitem')
        w.a(p, href=ri.link('wiki_head',path=path))
        w.pop()
        w.text('/')
    w.pop()

    
def content(w,h):
    w.push('div', id='main')
    w.write(h.wikifile.xhtml)
    w.pop()

'''
public templates
@template(title,nobot)
def hogehoge_body(w,h,parameters):

hogehoge_body(w,h.parameters) -> template(title,nobot)(hogehoge_body)(w,h,parameters)
'''
def template(title,nobot=False):
    def decorator(body):
        def inner(w,h,*args,**kw):
            ri = h.ri
            xmldec(w)
            w.push('html',**{'xmlns':'http://www.w3.org/1999/xhtml', 'xml:lang':'ja'})
            htmlheader(w,h,title+': '+h.title,nobot)
            w.push('body')
            
            header(w,h)
            menu(w,h)
    
            w.hr_full()
            w.push('div',id='body')
            body(w,h,*args, **kw)
            w.pop()
            w.hr_full()
    
            footer(w,h)

            w.pop()
            w.pop()
        return inner
    return decorator

@curry2
@template('Locked Page',True)
def locked_body(w,h):
    pathheader(w,h)
    w.hr()
    w.text('このページの編集はロックされています。')

@curry2
@template('')
def view_head_body(w,h):
    pathheader(w,h)
    w.hr()
    content(w,h)
    w.hr()

@curry2
@template('Old File',True)
def view_old_body(w,h):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    lmr = h.wikifile.lastmodified.revno
    w.textl('過去Revision表示モード。この内容は最新ではない可能性があります。')
    w.link_wiki('最新版を見る',ri.link('wiki_head',path=ri.path_info))
    w.hr()
    navi(w,h)
    w.hr()
    content(w,h)
    w.hr()

@curry2
@template('Upload File')
def attach_body(w,h,message,question):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    w.push('form',method='post', action='.', enctype='multipart/form-data')
    
    w.push('div')
    w.insertc('input',type='hidden', name='cmd', value='upload')
    w.insertc('input',type='file', size='100', name='file')
    w.pop()
    
    w.insertc('input', type='submit', value='Upload')
    
    w.pop()
    w.insert('p',message)

@curry2
@template('Uploaded',True)
def uploaded_body(w,h,success,message):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    if success:
        w.insert('p','upload成功')
    else:
        w.insert('p','upload失敗')
        w.insert('p',message)
    w.insert('p','Path: %s'%h.wikifile.path)
    w.a('ページへ行く',href='.')

@curry2
@template('Not Found',True)
def notfound_body(w,h):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    w.insert('p','このRevisionにこのページは存在しません。')
    w.a('現在のページを見にいく or 編集する',href=ri.link('wiki_head',path=h.wikifile.path))

@curry2
@template('Commited',True)
def commited_body(w,h,success,base_rev,commited_rev):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    if success:
        w.insert('p','commit成功')
        w.insert('p','この状態でリロードすると二重投稿になってしまいます。上のバーか、下のリンクから元のページへ飛んで下さい。')
    else:
        w.insert('p','commit失敗')
    w.push('p')
    w.text('Path: %s'%h.wikifile.path)
    w.br()
    w.text('Base Revision: %s' % base_rev)
    w.br()
    w.text('New Revision: %s' % commited_rev)
    w.pop()
    w.a('ページへ行く',href='.')

@curry2
@template('Post Comment',True)
def edit_comment_body(w,h,comment_no,author,comment_text,message,question):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    w.insert('p','Current Revision: %s' % h.wikifile.revno)
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
    
@curry2
@template('Edit',True)
def edit_body(w,h,preview_text,wiki_text,commitmsg_text,message,paraedit,question):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    w.insert('p','Current Revision: %s' % h.wikifile.revno)
    for m in message.splitlines():
        w.text(m)
        w.br()
    w.hr()
    w.push('form',method='post', action=h.ri.path_info, cls='editform')
    w.push('div')
    w.insertc('input',type='hidden', name='cmd', value='commit')
    w.insertc('input',type='hidden', name='base_rev', value=h.wikifile.revno)
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
    w.a('Wiki/Syntax',href=ri.link('wiki_head',path='Syntax.wiki'),cls='wiki')
    w.text('を参照してください。')
    w.text('大きな編集をする場合は')
    w.a('Wiki/編集ガイドライン',href=ri.link('wiki_head',path='Guideline.wiki'),cls='wiki')
    w.text('にも目を通して下さい。')
    w.pop()

    if preview_text:
        w.hr()
        w.push('div',id='main')
        w.write(preview_text)
        w.pop()

def navi(w,h):
    ri = h.ri
    w.link_wiki('通常の表示モードに戻る',ri.link('wiki_head',path=ri.path_info))
    w.hr()
    
    w.text('他Revisionナビゲーション:')
    
    lw = ListWriter(w)
    lw.move(1)
    w.text('Head')
    lw.move(2)
    rp = ri.link('wiki_rev',rev=h.wikifile.revno,path=h.wikifile.path)
    w.link_wiki('%s'%h.wikifile.revno,href=rp)
    w.text(', ')
    w.a('diff',href=rp+'?cmd=diff')

    lm = h.wikifile.lastmodified
    lw.move(1)
    w.text('Old Modified Revision:')
    w.br()
    for i in range(3):
        if not lm:
            break
        lw.move(2)
        rp = ri.link('wiki_rev',rev=lm.revno,path=lm.path)
        w.link_wiki('%s'%lm.revno,href=rp)
        w.text(', ')
        w.a('diff',href=rp+'?cmd=diff')
        lm = lm.previous
    
    lw.move(1)
    w.text('Old Revisions:')
    w.br()
    rev = h.wikifile.revno
    lw.move(2)
    w.text(str(h.wikifile.revno))
    for i in range(3):
        r = rev-1-i
        rr = h.wikifile.switch_rev(r)
        if not rr.exist:
            break
        rp = ri.link('wiki_rev',rev=rr.revno,path=rr.path)
        lw.move(2)
        w.link_wiki('%s'%r,href=rp)
        w.text(', ')
        w.a('diff',href=rp+'?cmd=diff')

    lw.finish()

@curry2
@template('Diff')
def diff_body(w,h,title,ffrom,fto,linediffs):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    navi(w,h)
    w.hr()
    w.push('div',id='main')
    w.push('div',cls='diff_text')
    w.insert('h1',title)
    if fto.changed:
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

@curry2
@template('History')
def history_body(w,h,offset):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    page_size = 25
    w.push('div',id='main')
    w.insert('h1','History of %s'%h.wikifile.path)

    w.push('span')
    w.a('younger',href='?cmd=history&offset=%s'%max(0,offset-page_size))
    w.text('|')
    w.a('older',href='?cmd=history&offset=%s'%(offset+page_size))
    w.pop()

    for index, hwp in enumerate(h.wikifile.history()):
        if offset < 0:
            break
        if index < offset:
            continue
        if offset + page_size <= index:
            break
    
        hrev = hwp.revno
        datetxt = hwp.revision.date.ctime()
        rp = ri.link('wiki_rev',rev=hwp.revno,path=hwp.path)

        w.push('h2')
        w.a('Revision %s'%hrev,href=rp)
        w.text(', ')
        w.a('diff',href=rp+'?cmd=diff')
        w.text(', '+datetxt)
        w.pop()
        nd = hwp.ndiff
        if None!=nd:
            if nd:
                format_ndiff(w,nd)
            else:
                w.insert('p','no changes')
    w.pop()

@curry2
@template('RecentChanges')
def recent_body(w,h,offset):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    page_size = 25
    w.push('div',id='main')
    w.insert('h1','Recent Changes')

    w.push('span')
    w.a('younger',href='?offset=%s'%max(0,offset-page_size))
    w.text('|')
    w.a('older',href='?offset=%s'%(offset+page_size))
    w.pop()

    for ind in range(page_size):
        rev = ri.head_rev-ind-offset
        if rev<=0:
            break

        datetxt = h.rev_date(rev).ctime()
        rtitle = 'Revision %s, %s' % (rev,datetxt)
        w.insert('h2',rtitle)
        for i,(internal_path,hwp,kind) in enumerate(h.changesets(rev)):
            if hwp:
                fname = hwp.path
                qa = ri.link('wiki_rev',rev=rev,path=hwp.path)
                dl = qa + '?cmd=diff'
                w.push('h3')
                w.text(kind+': ')
                w.a(fname,href=qa)
                w.text(', ')
                w.a('diff',href=dl)
                w.pop()
                nd = hwp.ndiff
                if None!=nd:
                    if nd:
                        format_ndiff(w,nd)
                    else:
                        w.insert('p','no changes')
            else:
                w.push('h3')
                w.text(kind+': ')
                w.text(internal_path)
                w.pop()
    w.pop()

@curry2
@template('Sitemap')
def sitemap_body(w,h):
    ri = h.ri
    pathheader(w,h)
    w.hr()
    w.push('div',id='main')
    w.insert('h1','SiteMap')

    rev = ri.head.last_paths_changed.revno
    lw = ListWriter(w)

    for wp, level in h.sitemap():
        lw.move(level+1)
        w.link_wiki(wp.path, href=ri.link('wiki_head',path=wp.path))

    w.pop()

@curry2
def sitemaptxt(w,h):
    ri = h.ri

    for wp,level in h.sitemap():
        w.text(ri.full_link('wiki_head',path=wp.path))
        w.write('\n')

@curry2
def atom(w,h):
    ri = h.ri
    import datetime, md5
    import utils.uuid as uuid
    def getid(s):
        return str(uuid.UUID(bytes=md5.md5(s).digest()))
    page_size = 30

    w.writel('<?xml version="1.0" encoding="utf-8"?>')
    w.push('feed',**{'xmlns':'http://www.w3.org/2005/Atom', 'xml:lang':'ja'})
    w.insert('title',h.ri.hostname)
    w.insert('subtitle',config.SITE_NAME)
    w.insert('id','urn:uuid:'+getid(h.ri.full_url_root+'/rss'))
    w.insert('updated',ri.head.date.isoformat()+'Z')
    w.insertc('link',href=h.ri.full_url_root)
    w.insertc('link',rel='self', href=ri.full_link('atom'))
    w.push('author')
    w.insert('name',config.AUTHOR)
    w.pop()
    for ind in range(page_size):
        rev = ri.head_rev-ind
        if rev <= 0:
            break
        for i,(internal_path,hwp,kind) in enumerate(h.changesets(rev)):
            if not hwp:
                continue
            rurl = ri.full_link('wiki_rev',rev=rev, path=path)
            title = 'Revision %s: %s: %s' % (rev,kind,hwp.path)
            pdate = hwp.revision.date

            qa = ri.link('wiki_rev',rev=rev, path=path)
            w.push('entry')
            w.insert('title',title,type='text')
            w.insert('id','urn:uuid:'+getid(rurl))
            w.insert('updated',pdate.isoformat()+'Z')
            w.insertc('link',href=rurl)

            nd = hwp.ndiff
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
