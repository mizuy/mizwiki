# -*- coding:utf-8 mode:Python -*-

from cStringIO import StringIO
from os import path
import difflib, datetime

from mizwiki import config, wiki2html, svnrep
from mizwiki.cache import cached, CacheSQL

#you must setting the connection before loading wikipage module.
#import sqlobject as so
#so.sqlhub.processConnection = so.connectionForURI('sqlite:' + config.cachedb)
cachef = CacheSQL()

def _internal_path(local_path):
    return path.join(config.svn_base,path.normpath(local_path))

def _calc_local_path(internal_path):
    b = config.svn_base.strip('/')
    i = internal_path.strip('/')
    if i.startswith(b):
        return i[len(b):].strip('/')
    return None


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

    def write(self, data, username, commitmsg, istext):
        return self._f.write(data, username, commitmsg, istext)
    
    @property
    def ndiff(self):
        if not self.previous:
            return None

        n = len(self.data)
        o = len(self.previous.data)
        return ' file size: from %s bytes to %s bytes' % (o,n)

    def page_exist(self,another_path):
        return self._f.revision.get_file(another_path).exist
    
    def history(self):
        for h in self._f.history():
            yield WikiFile.from_svnfile(h)

class WikiPage(WikiFile):
    '''
    specialized WikiFile class which handle revisionedfile whose extname is '.wiki'
    '''
    @property
    def depend_rev(self):
        '''
        revision on which this wikipage depends
        wikipage depends on the maximum of following two revision
        1. the lastmodified date of yourself
        2. the latest revision where paths_changed before yourself
        
        note: last_pahts_changes's computation complexity is O(number of revisions). memorize it.
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

    @cached(cachef, '_xhtml_')
    def _get_xhtml(self, path, dr):
        return wiki2html.wiki_to_xhtml(self.path, self.page_exist, self.data)

    @property
    def xhtml(self):
        return self._get_xhtml(self.path, self.depend_rev)

    def get_preview_xhtml(self, wiki_src):
        '''
        preview version of get_xhtml
        user wikisrc instead of self.read()
        '''
        return wiki2html.wiki_to_xhtml(self.path, self.page_exist, wiki_src)

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

    @cached(cachef,'_ndiff')
    def _get_ndiff(self, path, rev):
        n = self.data
        p = self.previous.data
        return '\n'.join(l for l in difflib.unified_diff(p.splitlines(),
                                                         n.splitlines()))
    @property
    def ndiff(self):
        if not self.previous:
            return None
        return self._get_ndiff(self.path, self.revno)

    def insert_comment(self, head_rev, username, commitmsg, comment_no, author, message):
        if not self.exist:
            return False
        datetext = datetime.datetime.now().ctime()
        outf = StringIO()
        ret = wiki2html.Comment.insert_comment(self.data,outf,comment_no,author,message,datetext)
        outf.seek(0)
        return self.write(outf.getvalue(), username, commitmsg, True)

    def get_paraedit_section(self, paraedit_from, paraedit_to):
        if not self.exist:
            return False
        return wiki2html.Paraedit.get_paraedit_section(self.data,paraedit_from,paraedit_to)        

    def get_paraedit_applied_data(self, paraedit_from, paraedit_to, wiki_src):
        if not self.exist:
            return False
        return wiki2html.Paraedit.apply_paraedit(self.data,paraedit_from,paraedit_to,wiki_src)

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

        return out,True,message
    else:
        return wiki_src,False,message

