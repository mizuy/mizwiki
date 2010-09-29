from mizwiki import urlmap, controllers

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
