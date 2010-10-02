# -*- coding:utf-8 mode:Python -*-
from werkzeug import exceptions

from xml.sax.saxutils import escape,unescape

import os
import re
from sets import Set
import rfc822, datetime

from mizwiki import misc,lang,views,page,urlmap

from mizwiki import config, htmlwriter, models, svnrep, requestinfo
from mizwiki.local import local

text_access_denied = 'Access Denied'

CONTENT_TYPE ={'.html':'text/html;charset=utf-8',
               '.atom':'application/atom+xml' }
CONTENT_TYPE.update(config.MIME_MAP)

class IterWriter(object):
    def __init__(self):
        self._l = []
    def write(self, text):
        self._l.append(text)
    def __iter__(self):
        #yield ''.join(self._l).encode('utf-8')
        for f in self._l:
            yield f.encode('utf-8')

class FileWrapper(object):
    def __init__(self, filelike, ext, headers=[]):
        if ext not in CONTENT_TYPE.keys():
            raise exceptions.Forbidden()
        self.headers = [('Content-Type',CONTENT_TYPE[ext])]+headers
        self.f = filelike
    def __call__(self, environ, start_response):
        start_response('200 OK', self.headers)
        if 'wsgi.file_wrapper' in environ:
            return environ['wsgi.file_wrapper'](self.f, config.BLOCK_SIZE)
        else:
            return iter(lambda: self.f.read(config.BLOCK_SIZE), '')

class RendererWrapper(object):
    def __init__(self, renderer, controller, content_type, headers=[]):
        self.headers = [('Content-Type',content_type)]+headers
        self.r = renderer
        self.h = controller
    def __call__(self, environ, start_response):
        start_response('200 OK', self.headers)
        iw = IterWriter()
        w = htmlwriter.WikiWriter(iw)
        self.r(w,self.h)
        return iw

class TextWrapper(object):
    def __init__(self, text, headers=[]):
        self.headers = headers
        self.text = text
    def __call__(self, environ, start_response):
        start_response('200 OK', [('Content-Type',CONTENT_TYPE['.txt'])]+self.headers)
        return [self.text]

class NotModified(exceptions.HTTPException):
    def __init__(self):
        pass
    def __call__(self, environ, start_response):
        start_response('304 NOT MODIFIED', [])
        return []


class Linker(object):
    def __init__(self, url_for, url_scheme, hostname, script_name, path_info):
        self.url_for = url_for
        self.url_scheme = url_scheme
        self.hostname = hostname
        self.script_name = script_name.strip('/')
        self.path_info = path_info.strip('/')

    @property
    def full_url_root(self):
        return self.url_scheme+'://'+self.hostname+'/'

    @property
    def full_tex_url(self):
        return self.full_url_root + 'cgi/mimetex.cgi'

    def full_link(self, name, **variables):
        return self.full_url_root + (self.script_name + '/').lstrip('/') + self.url_for(name, **variables)

    def link(self, name, **variables):
        return  misc.relpath(self.url_for(name, **variables), self.path_info)


re_cmd = re.compile('^cmd_(\w+)$')
class Controller(object):
    def __init__(self, path_info):
        self.sidebar_ = self.revision(self.head.revno).get_file('sidebar.wiki')
        self.linker = Linker(mapper.url_for, config.URL_SCHEME, config.HOSTNAME, config.SCRIPT_NAME, path_info)
        self.commands = {}
        for f in dir(self):
            m = re_cmd.match(f)
            if m:
                self.commands[m.group(1)] = getattr(self,f)

    sidebar = property(lambda x:x.sidebar_)

    def __call__(self, environ, start_response):
        self._headers = []
        ri = requestinfo.RequestInfo(environ)
        if not ri.args.has_key('cmd'):
            response = self.view(ri)
        else:
            try:
                response = self.commands[ri.args.get('cmd')](ri)
            except KeyError:
                raise exceptions.Forbidden()

        return response(environ, start_response)

    def view(self, ri):
        raise exceptions.Forbidden()

    def file_wrapper(self, filelike, ext):
        return FileWrapper(filelike, ext, self._headers)

    def renderer_wrapper(self, renderer, content_type=CONTENT_TYPE['.html']):
        return RendererWrapper(renderer, self, content_type, self._headers)

    def text_wrapper(self, text):
        return TextWrapper(text, self._headers)

    @property
    def lastmodified_date(self):
        raise NotImplemented

    @property
    def _lastmodified_date(self):
        lmd = self.lastmodified_date
        if config.GLOBAL_LASTMODIFIED_DATE:
            lmd = max(lmd, config.GLOBAL_LASTMODIFIED_DATE)
        return lmd

    def _lastmodified_headers(self, expire):
        r = self._lastmodified_date.ctime()
        h = []
        h.append(('Last-Modified',r))
        if expire:
            h.append(('Expires',r))
        return h

    def escape_if_clientcache(self, headers, expire=False):
        '''
        check the datetime of client cache, and lastmodified datetime of wiki page
        send back the lastmodified date, and
        send NotModified Code if you can use client cachef
        '''
        self._headers += self._lastmodified_headers(expire)
        
        ims = headers.get('If-Modified-Since')
        if not ims:
            return

        try:
            ccd = datetime.datetime(*rfc822.parsedate(ims)[:6])
        except:
            return

        if self._lastmodified_date <= ccd:
            raise NotModified()

    @property
    def title(self):
        return None

    @property
    def menu_items(self):
        #Set(['Head','History','Attach','Edit','View','Diff'])
        return Set()

    @property
    def repository(self):
        return local.repository

    def revision(self, revno):
        "need cache?"
        return local.repository.get_revision(revno)

    @property
    def head(self):
        return local.head


class ControllerWikiBase(Controller):
    def __init__(self, path_info, path='FrontPage.wiki', rev=None):
        super(ControllerWikiBase,self).__init__(path_info)
        self.path = path
        self.revno = int(rev) if rev else self.head.revno
        self.basepath = os.path.basename(path)
        self.wikifile_ = self.revision(self.revno).get_file(self.path)
        self.sidebar_ = self.revision(self.revno).get_file('sidebar.wiki')

    wikifile = property(lambda x:x.wikifile_)

    @property
    def title(self):
        return self.path

    @property
    def lastmodified_date(self):
        return self.wikifile.lastmodified.date

    def cmd_history(self, ri):
        if not self.wikifile.exist:
            raise exceptions.NotFound()
        self.escape_if_clientcache(ri.headers, True)
        offset = ri.args.get('offset',0,type=int)
        
        return self.renderer_wrapper(views.history_body(offset))

    def cmd_diff(self, ri):
        if not self.wikifile.exist:
            raise exceptions.NotFound()

        self.escape_if_clientcache(ri.headers, True)

        head_rev = self.head.revno
        target_rev = self.wikifile.revno

        f0 = self.wikifile.switch_rev(target_rev-1)
        f1 = self.wikifile.switch_rev(target_rev)
    
        if not f0.exist:
            f0lines = []
            f1lines = f1.text.splitlines()
            title = 'diff: none <==> Revision %s %s' % (f1.revno,self.title)
        else:
            # previous.path == lastmodified.path
            f0lines = f0.text.splitlines()
            f1lines = f1.text.splitlines()
            title = 'diff: Revision %s <==> Revision %s: %s' % (f0.revno,f1.revno,self.title)


        ld = misc.linediff(f0lines,f1lines)

        return self.renderer_wrapper(views.diff_body(title,f0,f1,ld))

class ControllerAttachFile(ControllerWikiBase):
    def view(self, ri):
        if not self.wikifile.exist:
            raise exceptions.NotFound()

        if not config.MIME_MAP.has_key(self.wikifile.ext):
            raise exceptions.Forbidden()

        self.escape_if_clientcache(ri.headers, False)

        return self.file_wrapper(self.wikifile.open(), self.wikifile.ext)

class ControllerWikiHead(ControllerWikiBase):
    @property
    def menu_items(self):
        if self.wikifile.exist:
            return Set(['Head','History','Attach','Edit','View','Diff'])
        else:
            return Set(['Edit'])

    def cmd_wordpress(self, ri):
        if self.wikifile.exist:
            self.escape_if_clientcache(ri.headers, True)
            return self.text_wrapper(self.wikifile.wordpress.encode('utf-8'))

    def view(self, ri):
        if self.wikifile.exist:
            self.escape_if_clientcache(ri.headers, True)
            return self.renderer_wrapper(views.view_head_body())
        else:
            return self.cmd_edit(ri)

    def _get_paraedit(self, dic):
        if dic.has_key('paraedit_from') and dic.has_key('paraedit_to'):
            return (dic.get('paraedit_from',type=int), dic.get('paraedit_to',type=int))
        else:
            return None

    def cmd_edit(self, ri):
        if not config.EDITABLE or self.wikifile.path in page.locked_pages:
            return self.renderer_wrapper(views.locked_body())

        paraedit = self._get_paraedit(ri.args)

        wikif = ''
        if self.wikifile.exist:
            if paraedit:
                wikif = self.wikifile.get_paraedit_section(paraedit[0],paraedit[1])
            else:
                wikif = self.wikifile.text

        #if wikif:
        #    wikif = wiki2html.pre_convert_wiki(wikif)

        return self.renderer_wrapper(views.edit_body('',wikif,'','',paraedit,not ri.is_valid_host))

    def cmd_commit(self, ri):
        form = ri.form

        if ri.is_spam:
            return self.text_wrapper(text_access_denied)
        if not config.EDITABLE or self.wikifile.path in page.locked_pages:
            return self.renderer_wrapper(views.locked_body())
        
        base_rev = form.get('base_rev',type=int)
        if not (base_rev<=self.head.revno) and base_rev > 0:
            raise exceptions.BadRequest()

        paraedit = self._get_paraedit(ri.form)

        wiki_text = unescape(form.get('text','')).replace('\r\n','\n')
        commitmsg_text = unescape(form.get('commitmsg',''))
        ispreview = form.has_key('preview')

        wiki_src_full = wiki_text
        if paraedit:
            wiki_src_full = self.wikifile.get_paraedit_applied_data(paraedit[0],paraedit[1],wiki_text)
        #wiki_src_full = wiki2html.pre_convert_wiki(wiki_src_full)

        base_page = self.wikifile.switch_rev(base_rev)
        full_merged,merged,message = models.merge_with_latest(self.wikifile,
                                                              base_page,
                                                              wiki_src_full)

        if merged or ispreview or (not ri.is_valid_host):
            if paraedit and not merged:
                edit_src = wiki_text
            else:
                edit_src = full_merged
                paraedit = None
            
            preview_text =  self.wikifile.get_preview_xhtml(edit_src)

            return self.renderer_wrapper(views.edit_body(preview_text,edit_src,commitmsg_text,
                                                         message,
                                                         paraedit,
                                                         not ri.is_valid_host))
        else:
            r = self.wikifile.write_text(full_merged, ri.user, commitmsg_text)
            return self.renderer_wrapper(views.commited_body(not not r,
                                                       base_rev=self.head.revno,
                                                             commited_rev=r))

    def cmd_comment(self, ri):
        form = ri.form
        if not self.wikifile.exist:
            raise exceptions.NotFound()

        if ri.is_spam or not config.EDITABLE:
            return self.text_wrapper(text_access_denied)

        author = unescape(form.get('author','AnonymousCorward')).strip()
        message = unescape(form.get('message','')).strip()
        comment_no = form.get('comment_no',type=int)

        if (not ri.is_valid_host) or (not message):
            return self.renderer_wrapper(views.edit_comment_body(comment_no,author,message,'',
                                                           not ri.is_valid_host))


        r = self.wikifile.insert_comment(self.head.revno, ri.user,
                               'comment by %s'% (author), comment_no, author, message)
        success = not not r

        return self.renderer_wrapper(views.commited_body(success,base_rev=self.head.revno,commited_rev=r))


    def page_attach(self,ri):
        ms = config.MAX_ATTACH_SIZE / 1024
        exts = ' '.join(list(config.MIME_MAP.keys()))
        message = lang.upload(ms,exts)

        return self.renderer_wrapper(views.attach_body(message,not ri.is_valid_host))

    def cmd_attach(self, ri):
        if not self.wikifile.exist:
            raise exceptions.NotFound()
        return self.page_attach(ri)

    def cmd_upload(self, ri):
        if not self.wikifile.exist:
            raise exceptions.NotFound()

        if ri.is_spam or not config.EDITABLE:
            return self.text_wrapper(text_access_denied)
        if not ri.is_valid_host:
            return self.page_attach(ri)
        
        filename = 'unkown'
        message = 'unkown error'
        success = False

        if not ri.files:
            message = 'no file.'
        else:
            item = ri.files['file']
            filename = os.path.basename(misc.normpath(item.filename.replace('\\','/'))).lower()
            ext = os.path.splitext(filename)[1]
            path = misc.join(self.wikifile.path,"../"+filename)
            wa = self.head.get_file(path)

            if not config.MIME_MAP.has_key(ext):
                message = '%s: file type not supported'%filename
            else:
                temp = misc.read_fs_file(item.stream, config.MAX_ATTACH_SIZE)
                if not temp:
                    message = '%s: too big file. maximum attach size = %s'%(filename,config.MAX_ATTACH_SIZE)
                else:
                    temp.seek(0)
                    success = not not wa.write(temp.read(), ri.user,
                                               'attach file uploaded', ext=='.txt')
                    if not success:
                        message = 'commit error.'

        if not success:
            ri.log('cmd_upload: file=%s message=%s'%(filename, message))
        return self.renderer_wrapper(views.uploaded_body(success,message))

class ControllerWikiRev(ControllerWikiBase):
    @property
    def menu_items(self):
        if self.wikifile.exist:
            return Set(['Head','View','Diff'])
        else:
            return Set(['Head'])
        
    @property
    def title(self):
        return 'Revision %s, %s'%(self.revno, self.path)

    def view(self, ri):
        if self.wikifile.exist:
            self.escape_if_clientcache(ri.headers, False)
            return self.renderer_wrapper(views.view_old_body())
        else:
            return self.renderer_wrapper(views.not_found_body())

class ControllerSitemap(Controller):
    @property
    def lastmodified_date(self):
        return self.head.last_paths_changed.date

    def view(self, ri):
        self.escape_if_clientcache(ri.headers, True)
        return self.renderer_wrapper(views.sitemap_body())

    def sitemap(self):
        rev = self.head.last_paths_changed.revno
        for n in self.revision(rev).ls_all:
            yield n

class ControllerSitemapText(ControllerSitemap):
    def view(self, ri):
        self.escape_if_clientcache(ri.headers, True)
        return self.renderer_wrapper(views.sitemaptxt(), CONTENT_TYPE['.txt'])

class ControllerRecentChanges(Controller):
    @property
    def lastmodified_date(self):
        return self.head.date

    def view(self, ri):
        self.escape_if_clientcache(ri.headers, True)
        offset = ri.args.get('offset',0,type=int)
        return self.renderer_wrapper(views.recent_body(offset))

    def rev_date(self,revno):
        return self.revision(revno).date
        
    def changesets(self,revno):
        for f,sets in self.revision(revno).paths_changed:
            s = sets.change_kind
            kind = svnrep.path_change[s]
            yield f, kind

class ControllerAtom(ControllerRecentChanges):
    def view(self, ri):
        self.escape_if_clientcache(ri.headers, True)
        return self.renderer_wrapper(views.atom(), CONTENT_TYPE['.atom'])

PWD = os.path.abspath(os.path.dirname(__file__))
class ControllerFile(Controller):
    def __init__(self, path_info, relative_path):
        super(ControllerFile,self).__init__(path_info)
        self.rpath = relative_path
        self.filepath = os.path.join(PWD,self.rpath)

    def view(self, ri):
        self.escape_if_clientcache(ri.headers)
        ext = os.path.splitext(self.rpath)[1]
        if not ext:
            raise exceptions.Forbidden
        f = open(self.filepath, 'r')
        return self.file_wrapper(f, ext)

    @property
    def lastmodified_date(self):
        return datetime.datetime.fromtimestamp(os.path.getmtime(self.filepath))

class ControllerTheme(ControllerFile):
    def __init__(self, path_info, path):
        super(ControllerTheme,self).__init__(path_info, misc.join('theme',path))

class ControllerFavicon(ControllerFile):
    def __init__(self, path_info):
        super(ControllerFavicon,self).__init__(path_info, 'favicon.ico')


mapper = urlmap.UrlMap()
mapper.add_rule('favicon.ico', ControllerFavicon, '^favicon.ico$', "%s")
mapper.add_rule('theme', ControllerTheme, '^theme/(.+)$', "theme/%s", ["path"])
mapper.add_rule('recentchanges', ControllerRecentChanges, 'RecentChanges$')
mapper.add_rule('atom', ControllerAtom, 'RecentChanges/atom.xml$')
mapper.add_rule('sitemap', ControllerSitemap, 'sitemap$')
mapper.add_rule('sitemap.txt', ControllerSitemapText, 'sitemap.txt$')

mapper.add_rule('frontpage', ControllerWikiHead, r'$', 'FrontPage.wiki')

mapper.add_rule('wiki_rev', ControllerWikiRev,
                r'r(\d+)/([\w_/+\-]+\.wiki)$', "r%d/%s",["rev","path"])
mapper.add_rule('wiki_head', ControllerWikiHead,
                r'([\w_/+\-]+\.wiki)$', "%s", ["path"])

mapper.add_rule('attach', ControllerAttachFile,
                r'r(\d+)/(/[\w_./+\-]*)$', "r%d/%s", ["rev","path"])
mapper.add_rule('attach', ControllerAttachFile,
                r'([\w_/+\-]+\.[\w_]+)$', "%s",["path"])

