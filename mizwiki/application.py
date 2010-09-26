from werkzeug import Request, ClosingIterator, exceptions

from mizwiki.local import local, local_manager

import re
from urllib import quote,unquote
from os import path
from mizwiki import controllers, urlmap, requestinfo

re_invalidchars = re.compile(r'[^\w_./+\-]',re.U)

mapper = urlmap.UrlMap()
mapper.add_rule('favicon.ico', controllers.ControllerFavicon, '^favicon.ico$', "%s")
mapper.add_rule('theme', controllers.ControllerTheme, '^theme/(.+)$', "theme/%s", ["path"])
mapper.add_rule('recentchanges', controllers.ControllerRecentChanges, 'RecentChanges$')
mapper.add_rule('atom', controllers.ControllerAtom, 'RecentChanges/atom.xml$')
mapper.add_rule('sitemap', controllers.ControllerSitemap, 'sitemap$')
mapper.add_rule('sitemap.txt', controllers.ControllerSitemapText, 'sitemap.txt$')

mapper.add_rule('frontpage', controllers.ControllerWikiHead, r'$', 'FrontPage.wiki')

mapper.add_rule('wiki_rev', controllers.ControllerWikiRev,
                r'r(\d+)/([\w_/+\-]+\.wiki)$', "r%d/%s",["rev","path"])
mapper.add_rule('wiki_head', controllers.ControllerWikiHead,
                r'([\w_/+\-]+\.wiki)$', "%s", ["path"])

mapper.add_rule('attach', controllers.ControllerAttachFile,
                r'r(\d+)/(/[\w_./+\-]*)$', "r%d/%s", ["rev","path"])
mapper.add_rule('attach', controllers.ControllerAttachFile,
                r'([\w_/+\-]+\.[\w_]+)$', "%s",["path"])

class MizWiki(object):
    def __init__(self):
        local.application = self

    def __call__(self, environ, start_response):
        local.application = self
        request = Request(environ)
        try:
            path_info = environ.get('PATH_INFO','/').strip('/')
            if re_invalidchars.search(path_info) != None:
                raise PathInfoException
            upath_info = unicode(unquote(path_info),'utf-8')

            controller = mapper.dispatch(upath_info)
            if not controller:
                raise exceptions.Forbidden()
    
            ri = requestinfo.RequestInfo(request, upath_info, mapper.url_for)
            response = controller(ri)
        except exceptions.HTTPException, e:
            response = e

        return ClosingIterator(response(environ, start_response),
                               [local_manager.cleanup])

application = MizWiki()
