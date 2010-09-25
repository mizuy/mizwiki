import wiki
from sets import Set
from xml.sax.saxutils import quoteattr,escape
from urllib import quote,unquote

indicator = '<#recent/>'

storage = '$recent$'
dep_recent = ':dep_recent:'

max_search_range = 100
max_entry = 20

def convert(doc,params,cv,ci):
    doc.add_dependancy(dep_recent)
    doc.write('\n'+indicator+'\n')

def post_convert(doc,cv,ci,rev):
    '''
    recent depends on its pages position deepness
    '''
    key = cv.get_globalrkey(storage+str(rev))
    if not cv.data_exist(key):
        d = doc.get_writer()
        render(d,rev,max_entry,ci)
        cv.data_save(key,d.getvalue())
    doc.write(cv.data_load(key))

def require_post_convert(deplist):
    return dep_recent in deplist

def render(doc,head_rev,num,ci):
    doc.push('div',cls='recentpage')
    i = 0
    rev = head_rev
    dd = None
    l = Set()
    while rev>(head_rev-max_search_range) and i<num:
        revd = wiki.wsvn.get_root(rev).date().date()
        for i,(path,hwp,kind) in enumerate(wiki.get_changesets(rev)):
            if hwp and hwp.exist():
                path = hwp.path.dirpath()
                fname = path.displayname()
                if fname not in l:
                    l.add(fname)
                    qa = ci.get_wiki_link(path)
                    if dd != revd:
                        dd = revd
                        doc.empathis(revd.isoformat())
                        doc.br()
                    doc.write('&nbsp;')
                    doc.link_wiki(escape(fname),href=qa)
                    doc.br()
                    i += 1
                    if i>=num:
                        break
        rev-=1
    doc.pop()

