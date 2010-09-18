# -*- coding:utf-8 mode:Python -*-

import wpath,config
Path = wpath.Path

FrontPage = Path('FrontPage/')
RecentChanges = Path('RecentChanges/')
Sitemap = Path('Sitemap/')
SitemapText = Path('Sitemap/txt/')
SideBar = Path('SideBar/')
top = Path()

Wiki = Path('Wiki/')
Syntax = Path('Wiki/Syntax/')
Guideline = Path('Wiki/編集ガイドライン/')

logo = Path('theme/logo.png')
style = Path('theme/style.css')
style_igb = Path('theme/style_igb.css')
atom = Path('RecentChanges/atom.xml')
valid_atom = Path('theme/valid-atom.png')
valid_xhtml = Path('theme/valid-xhtml10.png')
valid_css = Path('theme/valid-css.png')

DB = Path('DB/')
m = Path('DB/m/')
t = Path('DB/t/')

def full_url(p):
    return config.top_url.rstrip('/') + '/' + str(p)

locked_pages = [
    SideBar,
    ]
