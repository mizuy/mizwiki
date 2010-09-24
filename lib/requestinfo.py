# -*- coding:utf-8 mode:Python -*-

from mod_python import apache, util

from xml.sax.saxutils import escape,unescape
import rfc822, datetime
from hostvalidator import HostValidator
import config,misc
import svnrep
from os import path

class RequestInfo:
    def __repr__(self):
        return 'RequestInfo(ip=%s, %s)'%(self._ip,self.path_info)

    def __init__(self, req_, path_info, url_for):
        "http requests"
        self.req = req_
        self.fs = util.FieldStorage(req_)

        "svn repository"
        self.repo = svnrep.SvnRepository(config.repository_path)
        self.head = self.repo.youngest
        self.head_rev = self.head.revno

        "host validation"
        self._ip = self.req.get_remote_host(apache.REMOTE_NOLOOKUP)
        self._v = HostValidator(config.rbl_list, 
                                config.whitelist_ip,
                                config.blacklist,
                                config.spamblock,
                                lambda x:self.req.log_error(x,apache.APLOG_INFO))

        "path info"
        self.path_info = path_info
        self.url_for = url_for

    def full_link(self, name, **variables):
        return config.full_url(self.url_for(name, **variables))
    def link(self, name, **variables):
        ret = misc.relpath(self.url_for(name, **variables), self.path_info or '.')
        #self.log_debug('link %s %s -> %s'%(self.url_for(name, **variables), self.path_info or '.',ret))
        return ret

    @property
    def is_spam(self):
        "if spam, reject editing"
        return self._v.is_spam(self._ip)
    @property
    def is_valid_host(self):
        "if not spam but not valid_host, allow editing but reject committing without correct answer"
        return self._v.is_valid_host(self._ip)
    @property
    def user(self):
        return 'www-data@%s'%self._ip
    
    def escape_if_clientcache(self,lastmodified_date,expire):
        '''
        check the datetime of client cache, and lastmodified datetime of wiki page
        send back the lastmodified date, and
        send NotModified Code if you can use client cachef
        '''
        lmd = lastmodified_date
        if config.global_lastmodified_date:
            lmd = max(lmd, config.global_lastmodified_date)

        # you should send Last-Modified whether If-Modified-Since is presented or not
        r = lmd.ctime()
        self.req.headers_out['Last-Modified'] = r
        if expire:
            self.req.headers_out['Expires'] = r

        if not config.use_client_cache:
            return

        ims = self.req.headers_in.get('If-Modified-Since')
        if not ims:
            return
        try:
            ccd = datetime.datetime(*rfc822.parsedate(ims)[:6])
        except:
            return

        if lmd <= ccd:
            raise apache.SERVER_RETURN, apache.HTTP_NOT_MODIFIED

    def http_header(self, content_type):
        self.req.content_type = content_type
        self.req.send_http_header()

    def get_int(self, name):
        try:
            return int(self.fs.getfirst(name,'0'))
        except:
            raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

    def get_text(self, name):
        return unescape(self.fs.getfirst(name,''))
    def has_key(self, name):
        return self.fs.has_key(name)

    def log_debug(self, msg):
        self.req.log_error(msg,apache.APLOG_NOTICE)
