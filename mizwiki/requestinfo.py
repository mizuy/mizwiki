# -*- coding:utf-8 mode:Python -*-
from werkzeug import exceptions

from urllib import quote
from xml.sax.saxutils import escape,unescape
import rfc822, datetime
from os import path

from mizwiki.hostvalidator import HostValidator
from mizwiki import config, misc, svnrep

class RequestInfo:
    def __repr__(self):
        return 'RequestInfo(ip=%s, %s)'%(self._ip,self.path_info)

    def __init__(self, request, path_info, url_for):
        "http requests"
        self.req = request
        self.fs = request.args

        "svn repository"
        self.repo = svnrep.SvnRepository(config.repository_path)
        self.head = self.repo.youngest
        self.head_rev = self.head.revno

        "path info"
        self.path_info = path_info
        self.url_for = url_for

        self._logger = request.environ.get('wsgi.errors')

        "host validation"
        self._ip = self.req.remote_addr
        self._v = HostValidator(config.rbl_list, 
                                config.whitelist_ip,
                                config.blacklist,
                                config.spamblock,
                                self.log)

    @property
    def hostname(self):
        hostname = ''
        if self.req.environ.get('HTTP_HOST'):
            hostname += self.req.environ['HTTP_HOST']
        else:
            hostname += self.req.environ['SERVER_NAME']

            if self.req.environ['wsgi.url_scheme'] == 'https':
                if self.req.environ['SERVER_PORT'] != '443':
                    hostname += ':' + self.req.environ['SERVER_PORT']
                else:
                    if self.req.environ['SERVER_PORT'] != '80':
                        hostname += ':' + self.req.environ['SERVER_PORT']
        return hostname
        
    @property
    @misc.memorize
    def full_url_root(self):
        url = self.req.environ['wsgi.url_scheme']+'://'
        url += self.hostname
        return url

    @property
    def full_tex_url(self):
        return self.full_url_root + '/cgi/mimetex.cgi'

    def full_link(self, name, **variables):
        return self.full_url_root + quote(self.req.environ.get('SCRIPT_NAME', '')) + '/' + self.url_for(name, **variables)

    def link(self, name, **variables):
        return  misc.relpath(self.url_for(name, **variables), self.path_info or '.')

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
        '''disable'''
        return
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

        ims = self.req.headers.get('If-Modified-Since')
        if not ims:
            return
        try:
            ccd = datetime.datetime(*rfc822.parsedate(ims)[:6])
        except:
            return

        if lmd <= ccd:
            raise '304 NOT MODIFIED'

    def get_int(self, name):
        try:
            return int(self.fs.get(name,'0'))
        except:
            raise exceptions.BadRequest()

    def get_text(self, name):
        return unescape(self.fs.get(name,''))
    def has_key(self, name):
        return self.fs.has_key(name)

    def log(self, msg):
        if self._logger:
            self._logger.write(msg+'\n')
