# -*- coding:utf-8 mode:Python -*-

from mod_python import apache,util
import re
from urllib import quote,unquote
from os import path

import config
import controllers
import urlmap
from requestinfo import RequestInfo

def redirect(req,full_uri):
    req.headers_out['location'] = full_uri
    req.status = apache.HTTP_MOVED_TEMPORARILY
    return apache.OK

mapper = urlmap.UrlMap()
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

mapper.add_rule('theme', controllers.ControllerRecentChanges,
                'theme/(\w+)$', "theme/%s", ["path"])

class PathInfoException(Exception):
    pass

def _get_path_info(base_path, unparsed_uri):
    if not unparsed_uri:
        return ''
    else:
        uri = unparsed_uri.split('?')[0].lstrip('/')
        basep = base_path.lstrip('/')
        if uri.startswith(basep):
            return uri[len(basep):].strip('/')
        else:
            raise PathInfoException

def _to_unicode(path_info):
    try:
        return unicode(unquote(path_info),'utf-8')
    except:
        raise PathInfoException


re_theme = re.compile(r'^/theme',re.U)
re_invalidchars = re.compile(r'[^\w_./+\-]',re.U)

def start(req):
    def error(msg):
        req.log_error("DebugInfo: %s"%msg)
        
    if config.debug:
        req.log_error("DebugInfo: headers=%s"%str(req.headers_in))

    # escape theme/
    if re_theme.match(req.unparsed_uri):
        req.log_error("DebugInfo: DECLINED")
        return apache.DECLINED

    try:
        path_info = _get_path_info(config.w_path.strip('/'),req.unparsed_uri)
        if re_invalidchars.search(path_info) != None:
            raise PathInfoException
        upath_info = _to_unicode(path_info)
    except PathInfoException:
        req.log_error("PathInfoException: %s"%req.unparsed_uri)
        raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

    controller = mapper.dispatch(upath_info, error)
    if not controller:
        raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN
    
    ri = RequestInfo(req, upath_info, mapper.url_for)

    if config.debug:
        req.log_error("DebugInfo: unparsed_uri=%s"%req.unparsed_uri)
        req.log_error("DebugInfo: path_info=%s"%path_info)
        req.log_error("DebugInfo: upath_info=%s"%upath_info)
        req.log_error("DebugInfo: controller=%s"%controller(ri).__class__.__name__)
        req.log_error("DebugInfo: ri=%s"%ri)
    
    return controller(ri).execute()
