from mod_python import apache,util
import wiki,config,page
import re
from wpath import Path,join,split
from urllib import quote,unquote

from wikipage import wsvn

#import items

re_dirs = re.compile(r'/(\w[\w_+\-]*/)*(\w[\w_+\-]*)?$',re.U)
re_file = re.compile(r'/(\w[\w_+\-]*/)*\w[\w._+\-]*$',re.U)
re_invalidchars = re.compile(r'[^\w_./+\-]',re.U)
re_rev_path = re.compile(r'/r(\d+)(/[\w_./+\-]*)$',re.U)
re_theme    = re.compile(r'/theme',re.U)


def handler(req):
  if config.debug:
    req.log_error(str(req.headers_in))

  head_rev = wsvn.rev()

  if not req.unparsed_uri:
    path_info = '/'
  else:
    uri = req.unparsed_uri.split('?')[0]
    basep = '/'+config.w_path
    if uri.startswith(basep):
      path_info = uri[len(basep):]
    else:
      raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

  # escape theme/
  m = re_theme.match(path_info)
  if m:
    return apache.DECLINED

  # utf-8 check
  try:
    upath_info = unicode(unquote(path_info),'utf-8')
  except:
    raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

  # invalid path charactor
  if re_invalidchars.search(upath_info) != None: 
    raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

  m = re_rev_path.match(upath_info)
  if m:
    rev = int(m.group(1))
    headmode = False
    u_wikipage_path = m.group(2)
  else:
    rev = head_rev
    headmode = True
    u_wikipage_path = upath_info
    
  t_parts = split(u_wikipage_path.encode('utf-8'))
  if re_dirs.match(u_wikipage_path):
    p = Path.by_parts(t_parts,True)
  elif re_file.match(u_wikipage_path):
    p = Path.by_parts(t_parts,False)
  else:
    raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

  if p==Path():
    p = page.FrontPage
  elif p.parent()==Path() and p.isfile():
    raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

  ri = wiki.RequestInfo(req, path_info, head_rev, rev, headmode, p)

  if path_info != ri.normalized_path_info():
    if ri.fs.has_key('cmd'):
      raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST
    else:
      return wiki.redirect(req, ri.normalized_full_uri())

  h = None
  if ri.path == page.atom:
    h = wiki.HandlerAtom(ri)
  elif not ri.path.isdir():
    h = wiki.HandlerAttachFile(ri)
  elif ri.path == page.RecentChanges:
    h = wiki.HandlerRecentChanges(ri)
  elif ri.path == page.Sitemap:
    h = wiki.HandlerSitemap(ri)
  elif ri.path == page.SitemapText:
    h = wiki.HandlerSitemapText(ri)
  elif ri.headmode:
    h = wiki.HandlerWikiHead(ri)
  else:
    h = wiki.HandlerWikiRev(ri)

  if h:
    return h.execute()
  raise apache.SERVER_RETURN, apache.HTTP_FORBIDDEN
