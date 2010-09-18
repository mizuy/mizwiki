# -*- coding:utf-8 mode:Python -*-

from mod_python import apache,util
import time, string, cStringIO as StringIO, os, re, socket, difflib
import rfc822
from urllib import quote,unquote
from xml.sax.saxutils import quoteattr,escape,unescape

from sets import Set
import misc,lang,render,page
from wpath import Path,join,split

import config,wiki2html

from wikipage import WikiBase,WikiPage,WikiAttach,wsvn

text_access_denied = 'Access Denied'

# apache
def redirect(req,full_uri):
    req.headers_out['location'] = full_uri
    req.status = apache.HTTP_MOVED_TEMPORARILY
    return apache.OK

# interpret
def conv_int(string):
    try:
        return int(string)
    except:
        raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

class RequestInfo:
    def __init__(self, req_, path_info_, head_rev_, target_rev_, headmode_, path_):
        assert isinstance(path_,Path)
        self.fs = util.FieldStorage(req_)
        self.req = req_
        self.head_rev = head_rev_
        self.target_rev = target_rev_
        self.headmode = headmode_
        self.path = path_
        if path_.isdir():
            self.wp = WikiPage(target_rev_,path_)
        else:
            self.wp = WikiAttach(target_rev_,path_)
        self.path_info_ = path_info_
        self.link = Link(len(self.path.dirpath()),self.headmode)
        self._ip = self.req.get_remote_host(apache.REMOTE_NOLOOKUP)
        self._hostname_checked = False
        self._hostname = None
        self._white_list = self._ip in config.white_list_ip

    def svn_head(self):
        return wsvn.get_root(self.head_rev)
    
    def normalized_path_info(self):
        ret = '/'
        if not self.headmode:
            ret += 'r%s/'%self.target_rev
        ret += self.path.path()
        return quote(ret)
    def normalized_full_uri(self):
        return config.top_url.rstrip('/') + str(self.normalized_path_info())

    # http://mail.python.org/pipermail/python-list/2000-November/060249.html

    @staticmethod
    def is_in_rbl(ip, rbl_domain):
        l = string.split (ip, ".")
        l.reverse ()
        lookup_host = string.join (l, ".") + "." + rbl_domain
        try:
            addr = socket.gethostbyname (lookup_host)
        except socket.error:
            addr = ''
        # Some RBL-like lists use the returned addr to signify something,
        # so we'll return it.
        return addr

    def get_user(self):
        return 'www-data@%s'%self._ip

    def get_hostname(self):
        if self._hostname_checked:
            return self._hostname
        self._hostname_checked = True
        try:
            (hostname,a,b) = socket.gethostbyaddr(self._ip)
        except socket.error:
            return None

        self._hostname = hostname
        return hostname

    # if spam, rejest anyway
    def is_spam(self):
        ip = self._ip
        
        if not config.spamblock:
            self.req.log_error('is_spam(allow): spam block is disabled')
            return False
        if self._white_list:
            self.req.log_error('is_spam(allow): ip is in white_list: ip = %s'%ip)
            return False

        for rbl in config.rbl_list:
            if self.is_in_rbl(ip, rbl):
                self.req.log_error('is_spam: ip is in rbl: ip=%s rbl=%s'%(ip,rbl))
                return True

        # if in black list, reject anyway
        hostname = self.get_hostname()
        for bl in config.black_list:
            if hostname[-len(bl):]==bl:
                self.req.log_error('is_spam: ip is in black_list: ip=%s hostname=%s black_list=%s'%(ip,hostname,bl))
                return True

        self.req.log_error('is_spam(allow): ip is not in rbl or black_list: ip=%s'%ip)
        return False
    # elif valid_host, allow
    def is_valid_host(self):
        ip = self._ip

        if self._white_list:
            self.req.log_error('is_valid_host(allow): ip is in white_list: ip = %s'%ip)
            return True
        
        hostname = self.get_hostname()
        if not hostname:
            self.req.log_error('is_valid_host: ip has no hostname: ip = %s'%ip)
            return False

        if 'jp' != hostname.split('.')[-1]:
            self.req.log_error('is_valid_host: ip is not in .jp domain: ip=%s, hostname=%s'%(ip,hostname))
            return False

        self.req.log_error('is_valid_host(allow): ip has jp domain: ip=%s hostname=%s'%(ip,hostname))
        return True
    # elif valid_answer, allow
    def is_valid_answer(self):
        self.req.log_error('is_valid_answer: has not answer')
        return False
    # else, retry

    def get_clientcache_datetime(self):
        '''
        get the date of clientcache, private function
        '''
        ims = self.req.headers_in.get('If-Modified-Since')
        if not ims:
            return None
        try:
            return datetime.datetime(*rfc822.parsedate(ims)[:6])
        except:
            return None

    def check_clientcache(self,lastmodified_rev):
        '''
        check the datetime of client cache, and lastmodified datetime of wiki page
        send back the lastmodified date, and
        send NotModified Code if you can use client cachef
        '''
        lm = max(lastmodified_rev, config.global_lastmodified_rev)
        lmd = wsvn.get_root(lm).date()

        # you should send Last-Modified whether If-Modified-Since is presented or not
        r = lmd.ctime()
        self.req.headers_out['Last-Modified'] = r
        if self.headmode:
            self.req.headers_out['Expires'] = r

        if not config.use_client_cache:
            return False

        ccd = self.get_clientcache_datetime()
        if not ccd:
            return False

        if lmd <= ccd:
            raise apache.SERVER_RETURN, apache.HTTP_NOT_MODIFIED
        
    def local_link(self,p):
        return self.link.local_link(p)
    def head_link(self,p):
        return self.link.head_link(p)
    def rev_link(self,wp):
        return self.link.rev_link(wp)
    def full_rev_link(self,wp):
        return self.link.full_rev_link(wp)

class Link:
    def __init__(self,depth,headmode):
        '''
        self.depth = depth
        self.headmode = headmode
        '''
        self.local_depth = depth
        if headmode:
            self.head_depth = depth
        else:
            self.head_depth = 1+depth

    def local_link(self,p):
        assert isinstance(p,Path)
        return quote(str(Path.dotdot(self.local_depth) + p))
    def head_link(self,p):
        assert isinstance(p,Path)
        return quote(str(Path.dotdot(self.head_depth) + p))
    def rev_link(self,wp):
        assert isinstance(wp,WikiBase)
        return quote(str(Path.dotdot(self.head_depth) + wp.rev_path()))
    def full_rev_link(self,wp):
        assert isinstance(wp,WikiBase)
        return config.top_url.rstrip('/') + '/' + quote(str(wp.rev_path()))

class Handler(object):
    def execute(self):
        if not self.ri.fs.has_key('cmd'):
            return self.view()
        return self.command(self.ri.fs['cmd'])

    def check_clientcache(self):
        self.ri.check_clientcache(self.lastmodified_rev())
        
    def get_writer(self):
        return render.get_writer(self.ri.req)

    def __init__(self,ri):
        self.ri = ri

    def view(self):
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def command(self,cmd):
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def lastmodified_rev(self):
        assert False

    def title(self):
        return self.ri.path.displayname()

    def menu_items(self):
        #Set(['Head','History','Attach','Edit','View','Diff'])
        return Set()

    def render_preview(self,wiki_src):
        assert False
        
class HandlerAttachFile(Handler):
    def lastmodified_rev(self):
        return self.ri.wp.lastmodified_rev()

    def view(self):
        if not self.ri.wp.exist():
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
        return self.page_file()

    def page_file(self):
        if not config.mime_map.has_key(self.ri.wp.ext()):
            raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

        self.check_clientcache()

        self.ri.req.content_type = config.mime_map[self.ri.wp.ext()]
        self.ri.req.write(self.ri.wp.get_data())
        return apache.OK

class HandlerWikiHead(Handler):
    def lastmodified_rev(self):
        return self.ri.wp.lastmodified_rev()
        #sbp = WikiPage(self.ri.head_rev,page.SideBar).lastmodified_rev()
        #return max(p,sbp)

    def menu_items(self):
        if self.ri.wp.exist():
            return Set(['Head','History','Attach','Edit','View','Diff'])
        else:
            return Set(['Edit'])

    def view(self):
        assert self.ri.headmode

        if self.ri.wp.exist():
            return page_view(self)
        else:
            return page_edit(self)

    def command(self,cmd):
        assert self.ri.headmode

        if cmd=='edit':
            return page_edit(self)

        if cmd=='commit':
            return page_commit(self)

        if not self.ri.wp.exist():
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

        if cmd=='comment':
            return page_comment(self)

        if cmd=='history':
            return page_history(self)

        if cmd=='diff':
            return page_diff(self)

        if cmd=='attach':
            return page_attach(self)

        if cmd=='upload':
            return page_upload(self)

        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def render_preview(self,wiki_src):
        return self.ri.wp.get_preview_xhtml(wiki_src)

class HandlerWikiRev(Handler):
    def lastmodified_rev(self):
        p = self.ri.wp.lastmodified_rev()
        return p
        #sbp = WikiPage(self.ri.target_rev,page.SideBar).lastmodified_rev()
        #return max(p,sbp)

    def menu_items(self):
        if self.ri.wp.exist():
            return Set(['Head','View','Diff'])
        else:
            return Set(['Head'])

    def view(self):
        assert not self.ri.headmode

        if self.ri.wp.exist():
            return page_view(self)
        else:
            return page_notfound(self)

    def command(self,cmd):
        assert not self.ri.headmode

        if not self.ri.wp.exist():
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

        if cmd=='history':
            return page_history(self)

        if cmd=='diff':
            return page_diff(self)

        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

class HandlerRecentChanges(Handler):
    def lastmodified_rev(self):
        return self.ri.head_rev

    def view(self):
        if self.ri.headmode :
            return self.page_recent()
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def command(self,cmd):
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def page_recent(self):
        self.check_clientcache()

        offset = conv_int(self.ri.fs.getfirst('offset','0'))

        def body(w):
            render.recent_body(w,self.ri,offset)

        self.ri.req.content_type = render.content_type
        self.ri.req.send_http_header()
        w = self.get_writer()
        render.template(w,self,
                        title='RecentChanges',
                        nobot=True,
                        body=body)
        return apache.OK

class HandlerSitemap(Handler):
    def lastmodified_rev(self):
        return self.ri.svn_head().last_paths_changed_rev()

    def view(self):
        if self.ri.headmode :
            return self.page_sitemap()
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def command(self,cmd):
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def page_sitemap(self):
        self.check_clientcache()

        def body(w):
            render.sitemap_body(w,self.ri)

        self.ri.req.content_type = render.content_type
        self.ri.req.send_http_header()
        w = self.get_writer()
        render.template(w,self,
                        title='SiteMap',
                        nobot=True,
                        body=body)
        return apache.OK

class HandlerSitemapText(Handler):
    def lastmodified_rev(self):
        return self.ri.svn_head().last_paths_changed_rev()

    def view(self):
        if self.ri.headmode :
            return self.page_sitemap()
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def command(self,cmd):
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def page_sitemap(self):
        self.check_clientcache()

        self.ri.req.content_type = render.content_type_text
        self.ri.req.send_http_header()
        w = self.get_writer()
        render.sitemaptxt(w,self.ri)
        return apache.OK

class HandlerAtom(Handler):
    def lastmodified_rev(self):
        return self.ri.head_rev

    def view(self):
        if self.ri.headmode :
            return self.page_atom()
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def command(self,cmd):
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN

    def page_atom(self):
        self.check_clientcache()

        self.ri.req.content_type = 'application/atom+xml'
        self.ri.req.send_http_header()
        w = self.get_writer()
        render.atom(w,self.ri)

        return apache.OK

def page_attach(h):
    is_valid_host = h.ri.is_valid_host()
    
    ms = config.max_attach_size / 1024
    exts = string.join(list(config.mime_map.keys()),' ')
    message = lang.upload(ms,exts)

    w = h.get_writer()
    def body(w):
        render.attach_body(w,h.ri,message,not is_valid_host)
    h.ri.req.content_type = render.content_type
    h.ri.req.send_http_header()
    render.template(w,h,
                    title='Upload File: '+h.title(),
                    nobot=True,
                    body=body)
    return apache.OK

def read_fs_file(f,maxsize):
    temp = StringIO.StringIO()
    size = 0
    while True:
        size += 1024
        if size>maxsize:
            return None
        chunk = f.read(1024)
        if not chunk:
            break
        temp.write(chunk)
    return temp

def page_upload(h):
    assert isinstance(h,Handler)
    if h.ri.is_spam() or not config.editable:
        return debugtext(h.ri.req,text_access_denied)
    if not (h.ri.is_valid_host() or h.ri.is_valid_answer()):
        return page_attach(h)
        
    message = ''
    success = False

    if h.ri.fs.has_key('file'):
        item = h.ri.fs['file']
        if item.file:
            filename = os.path.basename(os.path.normpath(item.filename.replace('\\','/'))).lower()
            root,ext = os.path.splitext(filename)
            wa = h.ri.wp.get_attach(filename)

            if not config.mime_map.has_key(ext):
                message = '%s: file type not supported'%filename
            else:
                temp = read_fs_file(item.file,config.max_attach_size)
                if not temp:
                    message = '%s: too big file.'%filename
                else:
                    temp.seek(0)
                    success = not not wa.commit_data(h.ri.head_rev, h.ri.get_user(), 'attach file uploaded', temp, ext=='.txt')
                    if not success:
                        message = 'commit error.'

    def body(w):
        render.uploaded_body(w,h.ri,success,message)
    h.ri.req.content_type = render.content_type
    h.ri.req.send_http_header()
    w = h.get_writer()
    render.template(w,h,
                    title='Upload File: '+h.title(),
                    nobot=True,
                    body=body)
    return apache.OK

def page_comment(h):
    if h.ri.is_spam() or not config.editable:
        return debugtext(h.ri.req,text_access_denied)

    author = unescape(h.ri.fs.getfirst('author',''))
    message = unescape(h.ri.fs.getfirst('message',''))
    comment_no = conv_int(h.ri.fs.getfirst('comment_no','0'))

    if not author or author.isspace():
        author = 'AnonymousCoward'

    author = misc.igb_post_decode(author)
    message = misc.igb_post_decode(message)

    is_valid_host = h.ri.is_valid_host()
    is_valid_answer = h.ri.is_valid_answer()
    if (not (is_valid_host or is_valid_answer)) or (not message):
        if True:
            def body(w):
                render.edit_comment_body(w,h.ri,comment_no,author,message,'',not is_valid_host)
            h.ri.req.content_type = render.content_type
            h.ri.req.send_http_header()
            w = h.get_writer()
            render.template(w,h,
                            title='Post Comment: '+h.title(),
                            nobot=True,
                            body=body)
            return apache.OK

    success = h.ri.wp.insert_comment(h.ri.head_rev, h.ri.get_user(), 'comment by %s'% (author), comment_no, author, message)

    # error
    w = h.get_writer()
    if True:
        def body(w):
            render.commited_body(w,h.ri,success,base_rev=h.ri.head_rev,commited_rev=r)
        h.ri.req.content_type = render.content_type
        h.ri.req.send_http_header()
        render.template(w,h,
                        title='Commited: '+h.title(),
                        nobot=True,
                        body=body)

    return apache.OK

def page_edit(h):
    is_valid_host = h.ri.is_valid_host()

    #locked pages
    if not config.editable or h.ri.wp.path in page.locked_pages:
        h.ri.req.content_type = render.content_type
        h.ri.req.send_http_header()
        w = h.get_writer()
        def body(w):
            render.locked_body(w,h.ri)
        render.template(w,h,
                        title=h.title(),
                        nobot=True,
                        body=body)
        return apache.OK

    paraedit = None
    if h.ri.fs.has_key('paraedit_from') and h.ri.fs.has_key('paraedit_to'):
        paraedit_from = conv_int(h.ri.fs['paraedit_from'])
        paraedit_to = conv_int(h.ri.fs['paraedit_to'])
        paraedit = (paraedit_from,paraedit_to)

    wikif = ''
    if h.ri.wp.exist():
        if paraedit:
            wikif = h.ri.wp.get_paraedit_section(paraedit_from,paraedit_to)
        else:
            wikif = h.ri.wp.get_data()

    #if wikif:
    #wikif = wiki2html.pre_convert_wiki(wikif)
    
    def body(w):
        render.edit_body(w,h.ri,'',wikif,'','',paraedit,not is_valid_host)
    h.ri.req.content_type = render.content_type
    h.ri.req.send_http_header()
    w = h.get_writer()
    render.template(w,h,
                    title='Edit: '+h.title(),
                    nobot=True,
                    body=body)

    return apache.OK

def page_commit(h):
    if h.ri.is_spam():
        return debugtext(h.ri.req,text_access_denied)

    #locked pages
    if not config.editable or h.ri.wp.path in page.locked_pages:
        h.ri.req.content_type = render.content_type
        h.ri.req.send_http_header()
        w = h.get_writer()
        def body(w):
            render.locked_body(w,h)
        render.template(w,h.ri,
                        title=h.title(),
                        nobot=True,
                        body=body)
        return apache.OK

    # base_rev
    if not h.ri.fs.has_key('base_rev'):
        raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST
    base_rev = conv_int(h.ri.fs['base_rev'])
    if not (base_rev<=h.ri.head_rev):
        raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

    paraedit = None
    if h.ri.fs.has_key('paraedit_from') and h.ri.fs.has_key('paraedit_to'):
        paraedit_from = conv_int(h.ri.fs['paraedit_from'])
        paraedit_to = conv_int(h.ri.fs['paraedit_to'])
        paraedit = (paraedit_from,paraedit_to)

    wiki_text = unescape(h.ri.fs.getfirst('text',''))
    commitmsg_text = unescape(h.ri.fs.getfirst('commitmsg',''))
    ispreview = h.ri.fs.has_key('preview')

    if paraedit:
        wiki_src_full = h.ri.wp.get_paraedit_applied_data(paraedit_from,paraedit_to,wiki_text)
    else:
        wiki_src_full = wiki_text
    #wiki_src_full = wiki2html.pre_convert_wiki(wiki_src_full)

    full_merged,merged,message = merge_with_latest(h.ri.wp,wiki_src_full,base_rev,h.ri.head_rev)

    is_valid_host = h.ri.is_valid_host()
    is_valid_answer = h.ri.is_valid_answer()
        
    if merged or ispreview or (not (is_valid_host or is_valid_answer)):
        if paraedit:
            if merged:
                edit_src = full_merged
                paraedit = None
            else:
                edit_src = wiki_text
        else:
            edit_src = full_merged
            
        preview_text = h.render_preview(edit_src)

        def body(w):
            render.edit_body(w,h.ri,preview_text,edit_src,commitmsg_text,message,paraedit,not is_valid_host)
        h.ri.req.content_type = render.content_type
        h.ri.req.send_http_header()
        w = h.get_writer()
        render.template(w,h,
                        title='Edit: '+h.title(),
                        nobot=True,
                        body=body)
        return apache.OK
    else:
        r = h.ri.wp.commit_text(h.ri.head_rev, h.ri.get_user(), commitmsg_text, StringIO.StringIO(full_merged))
        success = not not r

        def body(w):
            render.commited_body(w,h.ri,success,base_rev=h.ri.head_rev,commited_rev=r)
        h.ri.req.content_type = render.content_type
        h.ri.req.send_http_header()
        w = h.get_writer()
        render.template(w,h,
                        title='Commited: '+h.title(),
                        nobot=True,
                        body=body)

        return apache.OK

def merge_with_latest(wp,wiki_src,base_rev,head_rev):
    '''
    merege wiki_src and head_revision if required.
    return 3 value tupple (wiki_src,Bool value indicating merged or not, merged_message)
    '''
    message = ''
    base_page = wp.switch_rev(base_rev)
    current_page = wp.lastmodified()

    if base_page.exist() and current_page and (base_rev < current_page.rev()):
        message = lang.conflict(base_rev,current_page.rev())
        base_data = base_page.get_data()
        current_data = current_page.get_data()

        l0 = 'Revision %s'%int(head_rev+1)
        l1 = 'Revision %s'%int(base_rev)
        l2 = 'Revision %s'%int(current_page.rev())

        code,out = misc.merge(wiki_src,base_data,current_data,l0,l1,l2)

        if code==0:
            message += lang.merge_success
        elif code==1:
            message += lang.merge_conflict
        else:
            message += lang.merge_error

        return out,True,message
    else:
        return wiki_src,False,message

def page_view(h):
    h.check_clientcache()

    def body(w):
        render.view_body(w,h.ri)
    h.ri.req.content_type = render.content_type
    h.ri.req.send_http_header()
    w = h.get_writer()
    render.template(w,h,
                    title=h.title(),
                    nobot=not h.ri.headmode,
                    body=body)

    return apache.OK

def page_diff(h):
    h.check_clientcache()

    head_rev = h.ri.head_rev
    target_rev = h.ri.wp.rev()

    f0 = h.ri.wp.switch_rev(target_rev-1)
    f1 = h.ri.wp.switch_rev(target_rev)
    changed = f1.changed()
    
    if not f0.exist():
        f0lines = []
        f1lines = f1.get_data().splitlines()
        title = 'diff: none <==> Revision %s %s' % (f1.rev(),h.title())
    else:
        # previous.path == lastmodified.path
        f0lines = f0.get_data().splitlines()
        f1lines = f1.get_data().splitlines()
        title = 'diff: Revision %s <==> Revision %s: %s' % (f0.rev(),f1.rev(),h.title())

    def linediff(fromlines,tolines):
        f = fromlines
        t = tolines
        m = difflib.SequenceMatcher(None, fromlines, tolines)

        for tag, i1, i2, j1, j2 in m.get_opcodes():
            fs = f[i1:i2]
            ts = t[j1:j2]
            if tag=='equal':
                for l in fs:
                    yield '',l
            elif tag=='replace':
                for l in fs:
                    yield 'del',l
                for l in ts:
                    yield 'new',l
            elif tag=='insert':
                for l in ts:
                    yield 'new',l
            elif tag=='delete':
                for l in fs:
                    yield 'del',l
            else:
                raise 'unreachable'

    ld = linediff(f0lines,f1lines)

    def body(w):
        render.diff_body(w,h.ri,title,f0,f1,ld)

    h.ri.req.content_type = render.content_type
    h.ri.req.send_http_header()
    w = h.get_writer()
    render.template(w, h,
                    title=title,
                    nobot=True,
                    body=body)
    return apache.OK

def page_history(h):
    h.check_clientcache()

    offset = conv_int(h.ri.fs.getfirst('offset','0'))

    def body(w):
        render.history_body(w,h.ri,offset)

    h.ri.req.content_type = render.content_type
    h.ri.req.send_http_header()
    w = h.get_writer()
    render.template(w,h,
                    title='History: '+h.title(),
                    nobot=True,
                    body=body)
    return apache.OK

def page_notfound(h):
    def body(w):
        render.notfound_body(w,h.ri)
    h.ri.req.content_type = render.content_type
    h.ri.req.send_http_header()
    w = h.get_writer()
    render.template(w,h,
                    title='Not Found: '+h.title(),
                    nobot=True,
                    body=body)
    return apache.OK

def debugtext(req,text):
    req.content_type = render.content_type_text
    req.send_http_header()
    req.write(text)
    return apache.OK
