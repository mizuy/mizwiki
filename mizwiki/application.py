from werkzeug import Request, ClosingIterator, exceptions

from mizwiki.local import local, local_manager

import re
from urllib import quote,unquote
from os import path
from mizwiki import controllers, mapper, requestinfo, config, models

re_invalidchars = re.compile(r'[^\w_./+\-]',re.U)

class MizWiki(object):
    def __init__(self,repository_path):
        self.repository_path = repository_path

    def __call__(self, environ, start_response):
        if not hasattr(local,'repository'):
            local.repository = models.Repository(self.repository_path)

        request = Request(environ)
        try:
            path_info = environ.get('PATH_INFO','/').strip('/')
            if re_invalidchars.search(path_info) != None:
                raise PathInfoException
            upath_info = unicode(unquote(path_info),'utf-8')

            controller = mapper.mapper.dispatch(upath_info)
            if not controller:
                raise exceptions.Forbidden()
    
            ri = requestinfo.RequestInfo(request)
            response = controller(ri)
        except exceptions.HTTPException, e:
            response = e

        return ClosingIterator(response(environ, start_response), [local_manager.cleanup])

application = MizWiki(config.REPOSITORY_PATH)
