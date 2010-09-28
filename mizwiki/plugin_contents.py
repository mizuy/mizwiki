import copy
import wiki2html
import htmlwriter, wikiparser

from cStringIO import StringIO

indicator = '<#contents/>'

class DocumentInterface_Title(wikiparser.WikiParserBase):
    def __init__(self,doc):
        self.doc = doc
        
    ########### Inline Elements ###########
    def br(self):
        pass
    def horizontal_line(self):
        pass
    def text(self,text):
        self.doc.text(text)
    def command(self,cmdname,params):
        pass
    def empathis(self,text):
        self.doc.empathis(text)
    def deleteline(self,text):
        self.doc.deleteline(text)
    def underline(self,text):
        self.doc.underline(text)

    ########### Link ###########
    # label maybe None
    def link_uri(self,label,uri):
        if label:
            self.doc.text(label)
        else:
            self.doc.text(uri)
    def link_wiki(self,label,wikiname,wikianame):
        if label:
            self.doc.text(label)
        else:
            self.doc.text(wikiname)
    
    # <a href=uri><img/></a>
    def link_img_uri(self,img_params,uri):
        pass
    def link_img_wiki(self,img_params,wikiname):
        pass
    
    ########### Foornote ###########
    def begin_footnote(self):
        pass
    def end_footnote(self):
        pass

    
class ContentsTable:
    def __init__(self):
        self.s = []
        self.out = StringIO()
        self.w = htmlwriter.WikiWriter(self.out)
        self.lw = htmlwriter.ListWriter(self.w)
        self.w.push('div',cls='contents')
        self.require_post_conversion = False

    def getvalue(self):
        return self.out.getvalue()
        
    def convert(self,doc):
        self.require_post_conversion = True
        doc.write('\n'+indicator+'\n')

    def finish(self):
        self.lw.finish()
        self.w.pop()

    def add_section(self, deep, title_parser, aname):
        if deep>3:
            return

        self.lw.move(deep)
        self.w.push('a',href='#'+aname,cls='wiki')
        title_parser(DocumentInterface_Title(self.w))
        self.w.pop()
