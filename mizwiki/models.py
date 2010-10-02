# -*- coding:utf-8 mode:Python -*-

from StringIO import StringIO
from os import path
import difflib, datetime

import os
from mizwiki import config, wiki2html, svnrep
from mizwiki.cache import CacheSQL
from mizwiki.wiki2wordpress import Wiki2Wordpress

class Wiki2HtmlWeb(wiki2html.Wiki2Html):
    def __init__(self, current_path, page_exist):
        super(Wiki2HtmlWeb, self).__init__()
        self.current_path = os.path.normpath(current_path)
        self.page_exist = page_exist
        
    def _make_label(self, label, wikiname):
        name = wikiname.replace(' ','_')
        path = os.path.normpath(name)
        if path.startswith('./') or path.startswith('../'):
            path = os.path.normpath(os.path.join(self.current_path, path))
        #self.add_linkto(path)
        
        if label:
            label = label.replace('_',' ')
        else:
            label = name
        return label, path
        
    def link_wiki(self,label,wikiname,wikianame):
        label, path = self._make_label(label,wikiname)
        if self.page_exist(path):
            self.w.link_wiki(label,path+wikianame)
        else:
            self.w.link_wikinotfound(label,path+wikianame)

class Wiki2HtmlWebAbsolute(Wiki2HtmlWeb):
    def link_wiki(self,label,wikiname,wikianame):
        label, path = self._make_label(label,wikiname)
        link = '/'+os.path.join(config.SCRIPT_NAME,path)
        if self.page_exist(path):
            self.w.link_wiki(label,link+wikianame)
        else:
            self.w.link_wikinotfound(label,link+wikianame)

cachef = CacheSQL()

def _internal_path(local_path):
    return path.join(config.SVN_BASE,path.normpath(local_path))

def _calc_local_path(internal_path):
    b = config.SVN_BASE.strip('/')
    i = internal_path.strip('/')
    if i.startswith(b):
        return i[len(b):].strip('/')
    return None

class Repository(object):
    def __init__(self, repository_path):
        self.repository = svnrep.SvnRepository(repository_path)
    def get_revision(self, revno):
        return Revision(self.repository, revno)
    @property
    def youngest(self):
        return self.repository.youngest

class Revision(object):
    def __init__(self, repository, revno):
        self.repository = repository
        self.revno = revno
        self.revision = self.repository.get_revision(self.revno)

    def get_file(self, path):
        return WikiFile.get(self.repository, self.revno, path)

    @property
    def ls_all(self):
        top = self.revision.get_file(config.SVN_BASE.strip('/'))
        for n in top.ls_all():
            f = WikiFile.from_svnfile(n)
            if f:
                yield f

    @property
    def date(self):
        return self.revision.date
    
    @property
    def paths_changed(self):
        for n,sets in self.revision.paths_changed:
            f = WikiFile.from_svnfile(n), sets
            if f:
                yield f
        

class WikiFile(object):
    '''
    Wrapper class for SvnRevisionedFile
    attach files and 
    
    WikiFile Creates WikiFile or WikiFilei nheritance based on the extname of revfile
    use WikiFile.generate(revfile) instead of __init__
    '''
    @classmethod
    def from_svnfile(cls, svnfile):
        if not svnfile:
            return None
        local_path = _calc_local_path(svnfile.path)
        if not local_path:
            return None
        if path.splitext(svnfile.path)[1]=='.wiki':
            return WikiPage(svnfile,local_path)
        else:
            return WikiFile(svnfile,local_path)

    @classmethod
    def get(cls, repo, revid, local_path):
        internal_path = _internal_path(local_path)
        svnfile = repo.get_revision(revid).get_file(internal_path)
        return WikiFile.from_svnfile( svnfile )

    def __init__(self, revfile, local_path):
        assert isinstance(revfile,svnrep.SvnFile)
        self._f = revfile
        self.path=local_path

    @property    
    def repo(self):
        return self._f.repository
    @property    
    def revision(self):
        return self._f.revision
    @property
    def svnfile(self):
        return self._f
    @property
    def revno(self):
        return self._f.revno
    @property
    def date(self):
        return self._f.revision.date
    @property
    def changed(self):
        return self._f.changed

    @property
    def lastmodified(self):
        return WikiFile.from_svnfile(self._f.lastmodified)
    @property
    def previous(self):
        return WikiFile.from_svnfile(self._f.previous)
    @property
    def exist(self):
        return self._f.exist

    def switch_rev(self,revno):
        return WikiFile.from_svnfile(self._f.switch_rev(revno))

    @property
    def data(self):
        return self._f.data

    def open(self):
        return self._f.open()
    
    @property
    def ext(self):
        return os.path.splitext(self.path)[1]

    def write(self, data, username, commitmsg, istext):
        #return self._f.write(data.replace('\r\n','\n'), username, commitmsg, istext)
        return self._f.write(data, username, commitmsg, istext)
    
    @property
    def ndiff(self):
        if not self.previous:
            return None

        n = len(self.data)
        o = len(self.previous.data)
        return ' file size: from %s bytes to %s bytes' % (o,n)

    def page_exist(self,another_path):
        return self._f.revision.get_file(_internal_path(another_path)).exist
    
    def history(self):
        for h in self._f.history():
            yield WikiFile.from_svnfile(h)

class WikiPage(WikiFile):
    '''
    specialized WikiFile class which handle revisionedfile whose extname is '.wiki'
    '''

    @property
    def text(self):
        return self.data.decode('utf-8').replace('\r\n','\n')

    def write_text(self, text, username, commitmsg):
        return self._f.write(text.replace('\r\n','\n').encode('utf-8'), username, commitmsg, True)

    @property
    def depend_rev(self):
        '''
        revision on which this wikipage depends
        wikipage depends on the maximum of following two revision
        1. the lastmodified date of yourself
        2. the latest revision where paths_changed before yourself
        
        note: last_pahts_changes's computation complexity is O(number of revisions). memoize it.
        '''
        r = self.repo.get_revision(self.revno)
        lpc = r.last_paths_changed.revno
        if self.exist:
            lmr = self.lastmodified.revno
        else:
            # TODO
            raise 'error'
            lmr = 0
        return max(lmr,lpc)

    @property
    def xhtml(self):
        return cachef.get_cachedata(
            repr((self.path,self.depend_rev)),
            lambda: Wiki2HtmlWeb(self.path, self.page_exist).parse(self.text))

    @property
    def xhtml_absolute(self):
        return cachef.get_cachedata(
            repr(('_xhtmlabs_',self.path,self.depend_rev)),
            lambda: Wiki2HtmlWebAbsolute(self.path, self.page_exist).parse(self.text))

    @property
    def wordpress(self):
        return Wiki2Wordpress().parse(self.text)

    def get_preview_xhtml(self, wiki_src):
        '''
        preview version of get_xhtml
        user wikisrc instead of self.read()
        '''
        return Wiki2HtmlWeb(self.path, self.page_exist).parse(wiki_src)

    @property
    def linkto(self):
        '''
        TODO:
        linkto list.
        list of the pages linked from me
        '''
        return []
    
    def get_brothers(self):
        for rf in self._f.brothers():
            r = WikiFile.from_svnfile(rf)
            if r:
                yield r

    @property
    def ndiff(self):
        if not self.previous:
            return None

        r = cachef.get_cachedata(
            repr(('ndiff',self.path,self.revno)),
            lambda:'\n'.join(l for l in difflib.unified_diff(
                    self.text.splitlines(),
                    self.previous.text.splitlines())))
        return r

    def insert_comment(self, head_rev, username, commitmsg, comment_no, author, message):
        if not self.exist:
            return False
        datetext = datetime.datetime.now().ctime()
        outf = StringIO()
        ret = wiki2html.Comment.insert_comment(self.text,outf,comment_no,author,message,datetext)
        outf.seek(0)
        return self.write(outf.getvalue(), username, commitmsg, True)

    def get_paraedit_section(self, paraedit_from, paraedit_to):
        if not self.exist:
            return False
        return wiki2html.Paraedit.get_paraedit_section(self.text,paraedit_from,paraedit_to)

    def get_paraedit_applied_data(self, paraedit_from, paraedit_to, wiki_src):
        if not self.exist:
            return False
        return wiki2html.Paraedit.apply_paraedit(self.text,paraedit_from,paraedit_to,wiki_src)

def merge_with_latest(wp, base_page, wiki_src):
    '''
    merege wiki_src and head_revision if required.
    return 3 value tupple (wiki_src,Bool value indicating merged or not, merged_message)
    '''
    message = ''
    current_page = wp.lastmodified

    if base_page.exist and current_page and (base_page.revno < current_page.revno):
        message = lang.conflict(base_page.revno,current_page.revno)

        l0 = 'Revision %s (new)'%int(wp.revno+1) # next revision
        l1 = 'Revision %s (your base)'%int(base_page.revno)
        l2 = 'Revision %s (another commit)'%int(current_page.revno)

        code,out = misc.merge(wiki_src,base_page.data,current_page.data,l0,l1,l2)

        if code==0:
            message += lang.merge_success
        elif code==1:
            message += lang.merge_conflict
        else:
            message += lang.merge_error

        return out.decode('utf-8'),True,message
    else:
        return wiki_src,False,message

