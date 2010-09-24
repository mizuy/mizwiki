# -*- coding:utf-8 mode:Python -*-

from os import path

def _p(a):
    path.normpath(a)

FrontPage = _p('FrontPage/')
SideBar = _p('SideBar/')
top = _p('')

Wiki = _p('Wiki/')
Syntax = _p('Wiki/Syntax/')
Guideline = _p('Wiki/編集ガイドライン/')

Atom = 'RecentChanges/atom.xml'
RecentChanges = 'RecentChanges'
Sitemap = 'sitemap'
SitemapText = 'sitemap.txt'

locked_pages = [
    SideBar,
    ]
