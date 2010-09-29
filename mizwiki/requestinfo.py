# -*- coding:utf-8 mode:Python -*-
from werkzeug import exceptions

from urllib import quote
from xml.sax.saxutils import escape,unescape
from os import path

from mizwiki.hostvalidator import HostValidator
from mizwiki import config, misc, svnrep
from mizwiki.local import local
from mizwiki.mapper import mapper

class RequestInfo:
    def __repr__(self):
        return 'RequestInfo(ip=%s, %s)'%(self._ip,self.path_info)

    def __init__(self, request):
        "http requests"
        self.req = request
        self.fs = request.args

        "svn repository"
        self.head = local.repository.youngest
        self.head_rev = self.head.revno

        self._logger = request.environ.get('wsgi.errors')

        self.path_info = request.environ.get('PATH_INFO','/').lstrip('/')
        self.url_for = mapper.url_for

        "host validation"
        self._ip = self.req.remote_addr or '0.0.0.0'
        self._v = HostValidator(config.RBL_LIST,
                                config.WHITELIST,
                                config.BLACKLIST,
                                config.SPAMBLOCK,
                                self.log)


    @property
    @misc.memorize
    def hostname(self):
        if config.HOSTNAME:
            return config.HOSTNAME
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
        return  misc.relpath(self.url_for(name, **variables), self.path_info)



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
    
    def log(self, msg):
        if self._logger:
            self._logger.write(msg+'\n')
