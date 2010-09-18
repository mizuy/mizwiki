import cStringIO as StringIO
from svn import fs as _fs
from wpath import Path,join,split
from urllib import quote,unquote

import os
import difflib,datetime
import svnrep
import config,wiki2html
import cache

# you must setting the connection before loading wikipage module.
#import sqlobject as so
#so.sqlhub.processConnection = so.connectionForURI('sqlite:' + config.cachedb)
cachef = cache.CacheSQL()
cachem = cache.CacheMem()

def localkey(rev,path,n=''):
    return str(Path('r%s/'%rev)+path)+str(n)

class CI(wiki2html.ConvertInterface):
    @classmethod
    def default(cls,rev,path):
        return CI(rev,path,len(path.dirpath()))

    def __init__(self,rev,path,linkpathn):
        self.rev = rev
        self.path = path
        self.depth = linkpathn

    def get_path(self):
        return self.path

    def page_exist(self,path):
        if path.isdir():
            wp = WikiPage(self.rev,path)
        else: 
            wp = WikiAttach(self.rev,path)
        return wp.exist()

    def get_wiki_link(self,path):
        assert isinstance(path,Path)
        if path==self.path:
            return quote(str(Path('.')))
        else:
            return quote(str(Path.dotdot(self.depth) + path))

    def get_wikisrc(self,path):
        wp = WikiPage(self.rev,path)
        return wp.get_data()

    def get_depth(self):
        return self.depth

# subversion repository
class WikiSvn:
    repo = svnrep.Repository(config.repository_path)
    roots = {}
    svn_base = Path.by_parts(config.svn_base)

    def rev(self):
        return self.repo.rev()
    def repository(self):
        return self.repo

    def get_root(self,rev):
        if not self.roots.has_key(rev):
            self.roots[rev] = svnrep.RevisionRoot(self.repo,rev)
        return self.roots[rev]

    def _get_svn_path(self,p):
        return str(self.svn_base + p)

    def get_revfile(self,rev,path):
        assert isinstance(rev,int)
        assert isinstance(path,Path)
        return svnrep.RevFile(self.get_root(rev),self._get_svn_path(path))

    @staticmethod
    def get_path(revfile):
        if not revfile:
            return None
        b = config.svn_base
        lb = len(b)
        parts = split(revfile.path())

        # if file is not exist, path is dir path
        isdir = True
        if revfile.isfile():
            isdir = False

        if len(parts)>lb:
            pb = parts[:lb]
            pa = parts[lb:]
            if pb==b:
                return Path.by_parts(pa,isdir)
        return None

kindmap = {
    _fs.path_change_modify: 'modified',
    _fs.path_change_add: 'added',
    _fs.path_change_delete: 'deleted',
    _fs.path_change_replace: 'replaced',
    _fs.path_change_reset: 'reset',
    }

def get_changesets(rev):
    changesets = wsvn.get_root(rev).paths_changed()
    for path,sets in changesets.iteritems():
        #sets.text_mod:

        s = sets.change_kind
        kind = str(s)
        if kindmap.has_key(s):
            kind = kindmap[s]

        revf = svnrep.RevFile(wsvn.get_root(rev),path)
        if revf.isfile():
            hwp = WikiBase.by_revfile(revf)
            yield path,hwp,kind


wsvn = WikiSvn()

class WikiBase(object):
    # TODO
    @classmethod
    def by_revfile(cls,revfile):
        if revfile.isdir():
            return WikiPage._by_revfile(revfile.child(config.bodytxt))
        elif revfile.basename()==config.bodytxt:
            return WikiPage._by_revfile(revfile)
        else:
            return WikiAttach._by_revfile(revfile)

    def __init__(self,revfile):
        assert isinstance(revfile,svnrep.RevFile)
        self._revfile = revfile

    def svn_root(self):
        return self._revfile.root()
    def rev(self):
        return self._revfile.rev()

    def get_data(self):
        return self._revfile.get_data()
    def exist(self):
        return self._revfile.exist()

    def lastmodified_rev(self):
        return self._revfile.lastmodified_rev()

    def lastmodified(self):
        return self._by_revfile(self._revfile.lastmodified())
    def previous(self):
        return self._by_revfile(self._revfile.previous())
    def history(self):
        for h in self._revfile.history():
            yield self._by_revfile(h)

    def changed(self):
        return self._revfile.changed()

    def switch_rev(self,rev):
        return self._by_revfile(self._revfile.switch_rev(rev))

    def svn_path(self):
        return self._revfile.path()

    def rev_path(self):
        return Path('r%s/'%self.rev())+ self.path

    def commit_data(self, head_rev, username, commitmsg, dataf, istext):
        '''
        commit a file to revfile,
        and return commited revision no.
        '''
        return wsvn.repository().putfile(head_rev,
                                      self.svn_path(),
                                      dataf,
                                      username,
                                      commitmsg,
                                      istext)

    def has_ndiff(self):
        return not not self._revfile.previous()

class WikiPage(WikiBase):
    @classmethod
    def _by_revfile(self,revfile):
        p = wsvn.get_path(revfile)
        if p:
            return WikiPage(revfile.rev(),p.parent())
        else:
            return None

    def __init__(self,rev,path):
        assert isinstance(path,Path)
        assert path.isdir()
        self.path = path
        super(WikiPage,self).__init__(wsvn.get_revfile(rev,path+config.bodytxt))
        self.cwc = None

        #def require_latest(self):
        #return False

    def lastmodified_rev(self):
        def lazy_eval():
            lpc = wsvn.get_root(self.rev()).last_paths_changed_rev()
            if self._revfile.exist():
                lmr = self._revfile.lastmodified_rev()
            else:
                lmr = self._revfile.rev()
            return str(max(lmr,lpc))
        key = localkey(self.rev(),self.path,'_depend_rev_')
        return int(cachem.get_cachedata(key,lazy_eval))

    def get_xhtml(self,ri):
        lmr = self.lastmodified_rev()
        def lazy_eval():
            ci = CI.default(lmr,self.path)
            xhtml = wiki2html.wiki_to_xhtml(ci,self.get_data())
            return xhtml
        key = localkey(lmr,self.path,'_xhtml_')
        return cachef.get_cachedata(key,lazy_eval)

    def get_preview_xhtml(self, wiki_src):
        lmr = self.lastmodified_rev()
        ci = CI.default(lmr,self.path)
        return wiki2html.wiki_to_xhtml(ci,wiki_src)

    def get_linkto(self):
        return []
    
    def get_attach(self,filename):
        return WikiAttach(self.rev(),self.path+filename)

    def get_attaches_and_children(self):
        attaches, children = self.get_attaches_and_children_path()
        rev = self.rev()
        a = [WikiAttach(rev,x) for x in attaches]
        c = [WikiPage(rev,x) for x in children]
        return a,c

    def get_attaches_and_children_path(self):
        parent = self._revfile.parent()
        rev = self.rev()
        attaches = []
        children = []
        for i in parent.ls():
            if i==config.bodytxt:
                continue

            rf = parent.child(i)
            p = self.path+i
            assert rf.exist()
            if rf.isfile():
                attaches.append(p.tofile())
            elif rf.isdir():
                children.append(p.todir())
            else:
                assert not 'unreachable'
        return attaches,children

    def get_ndiff(self):
        if not self.has_ndiff():
            return None

        def lazy_eval():
            pv = self.previous()
            buff = StringIO.StringIO()
            nl = self.get_data().splitlines()
            pl = pv.get_data().splitlines()
            for l in difflib.unified_diff(pl,nl):
                buff.write(l+'\n')
            return buff.getvalue()

        lk = localkey(self.rev(),self.path,'_ndiff')
        return cachef.get_cachedata(lk,lazy_eval)

    def insert_comment(self,head_rev,username,commitmsg,comment_no,author,message):
        if not self.exist():
            return False
        datetext = datetime.datetime.now().ctime()
        outf = StringIO.StringIO()
        ret = wiki2html.Comment.insert_comment(self.get_data(),outf,comment_no,author,message,datetext)
        outf.seek(0)
        return self.commit_data(head_rev, username, commitmsg, outf, True)

    def get_paraedit_section(self, paraedit_from, paraedit_to):
        if not self.exist():
            return False
        return wiki2html.Paraedit.get_paraedit_section(self.get_data(),paraedit_from,paraedit_to)        

    def get_paraedit_applied_data(self, paraedit_from, paraedit_to, wiki_src):
        if not self.exist():
            return False
        return wiki2html.Paraedit.apply_paraedit(self.get_data(),paraedit_from,paraedit_to,wiki_src)

    def commit_text(self, head_rev, username, commitmsg, textf):
        return self.commit_data(head_rev, username, commitmsg, textf, True)


class WikiAttach(WikiBase):
    @classmethod
    def _by_revfile(cls,revfile):
        r = revfile.rev()
        p = wsvn.get_path(revfile)
        if p:
            return WikiAttach(r,p)
        else:
            return None
    
    def __init__(self,rev,path):
        assert isinstance(path,Path)
        self.path = path
        super(WikiAttach,self).__init__(wsvn.get_revfile(rev,path))

    def ext(self):
        root,e = os.path.splitext(self.path.basename())
        return e.lower()

    def get_ndiff(self):
        if not self.has_ndiff():
            return None

        n = len(self.get_data())
        o = len(self.previous().get_data())

        return '  file size: from %s bytes to %s bytes' % (o,n)
