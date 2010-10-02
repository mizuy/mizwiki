# -*- coding:utf-8 mode:Python -*-
from werkzeug import exceptions

from urllib import quote
from xml.sax.saxutils import escape,unescape

from mizwiki.hostvalidator import HostValidator
from mizwiki import config, misc, svnrep
from mizwiki.local import local

from werkzeug import BaseRequest

class RequestInfo(BaseRequest):
    def __init__(self,environ):
        super(RequestInfo, self).__init__(environ)

        "logger"
        self._logger = self.environ.get('wsgi.errors')

        "host validation"
        self._ip = self.remote_addr or '0.0.0.0'
        self._v = HostValidator(config.RBL_LIST,
                                config.WHITELIST,
                                config.BLACKLIST,
                                config.SPAMBLOCK,
                                self.log)


    @property
    @misc.memoize
    def hostname(self):
        hostname = ''
        if self.environ.get('HTTP_HOST'):
            hostname += self.environ['HTTP_HOST']
        else:
            hostname += self.environ['SERVER_NAME']

            if self.environ['wsgi.url_scheme'] == 'https':
                if self.environ['SERVER_PORT'] != '443':
                    hostname += ':' + self.environ['SERVER_PORT']
                else:
                    if self.environ['SERVER_PORT'] != '80':
                        hostname += ':' + self.environ['SERVER_PORT']
        return hostname
        
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
