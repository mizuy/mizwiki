# -*- coding:utf-8 mode:Python -*-
from werkzeug import exceptions

from cStringIO import StringIO
import os
from os import path
import re
from sets import Set

from mizwiki import misc,lang,views,page
from mizwiki.misc import memorize

from mizwiki import config, htmlwriter, models, svnrep

text_access_denied = 'Access Denied'

class IterWriter(object):
    def __init__(self):
        self._l = []
    def write(self, text):
        self._l.append(str(text))
    def __iter__(self):
        for f in self._l:
            yield f

class FileWrapper(object):
    def __init__(self, filelike, content_type):
        self.c = content_type
        self.f = filelike
    def __call__(self, environ, start_response):
        start_response('200 OK', [('Content-type',self.c)])
        if 'wsgi.file_wrapper' in environ:
            return environ['wsgi.file_wrapper'](self.f, config.BLOCK_SIZE)
        else:
            return iter(lambda: self.f.read(config.BLOCK_SIZE), '')

class RendererWrapper(object):
    def __init__(self, renderer, controller, content_type=views.content_type):
        self.r = renderer
        self.c = content_type
        self.h = controller
    def __call__(self, environ, start_response):
        start_response('200 OK', [('Content-type',self.c)])
        iw = IterWriter()
        w = htmlwriter.WikiWriter(iw)
        self.r(w,self.h)
        return iw

class TextWrapper(object):
    def __init__(self, text):
        self.text = text
    def __call__(self, environ, start_response):
        start_response('200 OK', [('Content-type',views.content_type_text)])
        return [self.text]


re_cmd = re.compile('^cmd_(\w+)$')
class Controller(object):
    def __init__(self, ri):
        self.ri = ri
        self.commands = {}
        for f in dir(self):
            m = re_cmd.match(f)
            if m:
                self.commands[m.group(1)] = getattr(self,f)
        
    def __call__(self, environ, start_response):
        if not self.ri.has_key('cmd'):
            response = self.view()
        else:
            try:
                cmd = self.commands[self.ri.get_text('cmd')]
                response = cmd()
            except KeyError:
                raise exceptions.Forbidden()

        return response(environ, start_response)

    def escape_if_clientcache(self,expire=False):
        self.ri.escape_if_clientcache(self.lastmodified_date,expire)

    def view(self):
        raise exceptions.Forbidden()

    @property
    def lastmodified_date(self):
        assert None

    @property
    def title(self):
        return self.ri.path_info

    @property
    def menu_links(self):
        return {
            'History':'?cmd=history',
            'Attach':'?cmd=attach',
            'Edit':'?cmd=edit',
            'Source':"?cmd=viewsrc",
            'Diff':"?cmd=diff",
            }

    @property
    def menu_items(self):
        #Set(['Head','History','Attach','Edit','View','Diff'])
        return Set()

class ControllerWikiBase(Controller):
    def __init__(self, ri, path='FrontPage.wiki', rev=None):
        super(ControllerWikiBase,self).__init__(ri)
        self.path = path
        self.wikifile_ = models.WikiFile.get(self.ri.repo, int(rev) if rev else ri.head_rev, self.path)
    wikifile = property(lambda x:x.wikifile_)

    @property
    @memorize
    def menu_links(self):
        v = super(ControllerWikiBase,self).menu_links
        v.update({'Head': self.ri.link('wiki_head',path=self.wikifile.path),
                  'View': self.ri.link('wiki_head',path=self.wikifile.path)})
        return v

    @property
    def lastmodified_date(self):
        return self.wikifile.lastmodified.date

    def cmd_history(self):
        if not self.wikifile.exist:
            raise exceptions.NotFound()
        self.escape_if_clientcache(True)
        offset = self.ri.get_int('offset')
        
        return RendererWrapper(views.history_body(offset), self)

    def cmd_diff(self):
        if not self.wikifile.exist:
            raise exceptions.NotFound()

        self.escape_if_clientcache(True)

        head_rev = self.ri.head_rev
        target_rev = self.wikifile.revno

        f0 = self.wikifile.switch_rev(target_rev-1)
        f1 = self.wikifile.switch_rev(target_rev)
    
        if not f0.exist:
            f0lines = []
            f1lines = f1.data.splitlines()
            title = 'diff: none <==> Revision %s %s' % (f1.revno,self.title)
        else:
            # previous.path == lastmodified.path
            f0lines = f0.data.splitlines()
            f1lines = f1.data.splitlines()
            title = 'diff: Revision %s <==> Revision %s: %s' % (f0.revno,f1.revno,self.title)


        ld = misc.linediff(f0lines,f1lines)

        return RendererWrapper(views.diff_body(title,f0,f1,ld), self)

class ControllerAttachFile(ControllerWikiBase):
    def view(self):
        if not self.wikifile.exist:
            raise exceptions.NotFound()

        if not config.MIME_MAP.has_key(self.wikifile.ext()):
            raise exceptions.Forbidden()

        self.excape_if_clientcache()

        return FileWrapper(self.wikifile.open(), config.MIME_MAP[self.wikifile.ext()])

class ControllerWikiHead(ControllerWikiBase):
    @property
    def menu_items(self):
        if self.wikifile.exist:
            return Set(['Head','History','Attach','Edit','View','Diff'])
        else:
            return Set(['Edit'])

    def view(self):
        if self.wikifile.exist:
            self.escape_if_clientcache(True)
            return RendererWrapper(views.view_head_body(), self)
        else:
            return self.cmd_edit()

    def get_paraedit(self):
        if self.ri.has_key('paraedit_from') and self.ri.has_key('paraedit_to'):
            return (self.ri.get_int('paraedit_from'), self.ri.get_int('paraedit_to'))
        return None

    def cmd_edit(self):
        if not config.EDITABLE or self.wikifile.path in page.locked_pages:
            return RendererWrapper(views.locked_body(), self)

        paraedit = self.get_paraedit()

        wikif = ''
        if self.wikifile.exist:
            if paraedit:
                wikif = self.wikifile.get_paraedit_section(paraedit[0],paraedit[1])
            else:
                wikif = self.wikifile.data

        #if wikif:
        #    wikif = wiki2html.pre_convert_wiki(wikif)

        return RendererWrapper(views.edit_body('',wikif,'','',paraedit,not self.ri.is_valid_host), self)

    def cmd_commit(self):
        if self.ri.is_spam:
            return debugtext(self.ri.req,text_access_denied)
        if not config.EDITABLE or self.wikifile.path in page.locked_pages:
            return RendererWrapper(views.locked_body(), self)
        
        base_rev = self.ri.get_int('base_rev')
        if not (base_rev<=self.ri.head_rev) and base_rev > 0:
            raise exceptions.BadRequest()

        paraedit = self.get_paraedit()

        wiki_text = self.ri.get_text('text')
        commitmsg_text = self.ri.get_text('commitmsg')
        ispreview = self.ri.has_key('preview')

        wiki_src_full = wiki_text
        if paraedit:
            wiki_src_full = self.wikifile.get_paraedit_applied_data(paraedit[0],paraedit[1],wiki_text)
        #wiki_src_full = wiki2html.pre_convert_wiki(wiki_src_full)

        base_page = self.wikifile.switch_rev(base_rev)
        full_merged,merged,message = models.merge_with_latest(self.wikifile,
                                                              base_page,
                                                              wiki_src_full)

        if merged or ispreview or (not self.ri.is_valid_host):
            if paraedit and not merged:
                edit_src = wiki_text
                full_edit = False
            else:
                edit_src = full_merged
                full_edit = True
            
            preview_text =  self.wikifile.get_preview_xhtml(edit_src)

            return RendererWrapper(views.edit_body(preview_text,edit_src,commitmsg_text,
                                                   message,not full_edit,not self.ri.is_valid_host),
                                   self)
        else:
            r = self.wikifile.write(full_merged,
                                    self.ri.user,
                                    commitmsg_text,True)
            return RendererWrapper(views.commited_body(not not r,
                                                       base_rev=self.ri.head_rev,
                                                       commited_rev=r.revno), self)

    def cmd_comment(self):
        if not self.wikifile.exist:
            raise exceptions.NotFound()

        if self.ri.is_spam or not config.EDITABLE:
            return debugtext(self.ri.req,text_access_denied)

        author = self.ri.get_text('author').strip() or 'AnonymousCoward'
        message = self.ri.get_text('message').strip()
        comment_no = self.ri.get_int('comment_no')

        if (not self.ri.is_valid_host) or (not message):
            return RendererWrapper(views.edit_comment_body(comment_no,author,message,'',
                                                           not self.ri.is_valid_host), self)


        r = self.wikifile.insert_comment(self.ri.head_rev, self.ri.user,
                               'comment by %s'% (author), comment_no, author, message)
        success = not not r

        return RendererWrapper(views.commited_body(success,base_rev=self.ri.head_rev,commited_rev=r), self)


    def page_attach(self):
        ms = config.MAX_ATTACH_SIZE / 1024
        exts = ' '.join(list(config.MIME_MAP.keys()))
        message = lang.upload(ms,exts)

        return RendererWrapper(views.attach_body(message,not self.ri.is_valid_host), self)

    def cmd_attach(self):
        if not self.wikifile.exist:
            raise exceptions.NotFound()
        return self.page_attach()

    def cmd_upload(self):
        if not self.wikifile.exist:
            raise exceptions.NotFound()

        if self.ri.is_spam or not config.EDITABLE:
            return debugtext(self.ri.req,text_access_denied)
        if not self.ri.is_valid_host:
            return self.page_attach()
        
        message = ''
        success = False

        if self.ri.has_key('file'):
            item = self.ri.fs['file']
            if item.file:
                filename = path.basename(path.normpath(item.filename.replace('\\','/'))).lower()
                root,ext = path.splitext(filename)
                wa = self.wikifile.get_attach(filename)

                if not config.MIME_MAP.has_key(ext):
                    message = '%s: file type not supported'%filename
                else:
                    temp = misc.read_fs_file(item.file,config.MAX_ATTACH_SIZE)
                    if not temp:
                        message = '%s: too big file.'%filename
                    else:
                        temp.seek(0)
                        success = not not wa.write(temp.read(), self.ri.user,
                                                   'attach file uploaded', ext=='.txt')
                        if not success:
                            message = 'commit error.'

                            
        return RendererWrapper(views.uploaded_body(success,message), self)

class ControllerWikiRev(ControllerWikiBase):
    @property
    def menu_items(self):
        if self.wikifile.exist:
            return Set(['Head','View','Diff'])
        else:
            return Set(['Head'])

    def view(self):
        if self.wikifile.exist:
            self.escape_if_clientcache(False)
            return RendererWrapper(views.view_old_body(), self)
        else:
            return RendererWrapper(views.not_found_body(), self)

class ControllerSitemap(Controller):
    @property
    def lastmodified_date(self):
        return self.ri.head.last_paths_changed.date

    def view(self):
        self.escape_if_clientcache(True)
        return RendererWrapper(views.sitemap_body(), self)

    def sitemap(self):
        rev = self.ri.head.last_paths_changed.revno
        revision = self.ri.repo.get_revision(rev)
        top = revision.get_file(config.SVN_BASE.strip('/'))
        for n,l in top.ls_all():
            yield models.WikiFile.from_svnfile(n), l

class ControllerSitemapText(ControllerSitemap):
    def view(self):
        self.escape_if_clientcache(True)
        return RendererWrapper(views.sitemaptxt(), self)

class ControllerRecentChanges(Controller):
    @property
    def lastmodified_date(self):
        return self.ri.head.date

    def view(self):
        self.escape_if_clientcache(True)
        offset = self.ri.get_int('offset')
        return RendererWrapper(views.recent_body(offset), self)

    def rev_date(self,revno):
        return self.ri.repo.get_revision(revno).date
        
    def changesets(self,revno):
        revision = self.ri.repo.get_revision(revno)
        for f,sets in revision.paths_changed:
            s = sets.change_kind
            if svnrep.path_change.has_key(s):
                kind = svnrep.path_change[s]
            yield f.path,models.WikiFile.from_svnfile(f), kind

class ControllerAtom(ControllerRecentChanges):
    def view(self):
        self.escape_if_clientcache(True)
        return RendererWrapper(views.atom(), self, 'application/atom+xml')

class ControllerFile(Controller):
    def __init__(self, ri, relative_path):
        super(ControllerFile,self).__init__(ri)
        self.rpath = relative_path
    def view(self):
        ext = path.splitext(self.rpath)[1]
        if not ext:
            raise exceptions.Forbidden
        f = open(path.join(path.abspath(path.dirname(__file__)),self.rpath), 'r')
        return FileWrapper(f, config.MIME_MAP[ext])

class ControllerTheme(ControllerFile):
    def __init__(self, ri, path):
        super(ControllerTheme,self).__init__(ri, os.path.join('theme',path))

class ControllerFavicon(ControllerFile):
    def __init__(self, ri):
        super(ControllerFavicon,self).__init__(ri,'favicon.ico')