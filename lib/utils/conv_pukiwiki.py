# -*- coding: utf-8 -*-
import codecs, os, cStringIO as StringIO, re, sys

class IStreamBuffer:
    @staticmethod
    def _conv(v):
        return v.rstrip(u'\n\r')
    
    def __init__(self,inputfile):
        self.input = codecs.getreader('utf-8')(inputfile)
        self.stack = []

    def __iter__(self):
        return self

    def next(self):
        if len(self.stack)>0:
            return self._conv(self.stack.pop())
        return self._conv(self.input.next())

    def push(self,line):
        self.stack.append(self._conv(line))

    def eof(self):
        if len(self.stack)==0:
            try:
                self.push(self.input.next())
            except StopIteration:
                return True
        return False
            
    def top(self):
        assert not self.eof()
        if len(self.stack)==0:
            self.push(self.input.next())
        return self.stack[-1]


def conv(inputs,os):
    os = codecs.getwriter('utf-8')(os)
    istr = IStreamBuffer(inputs)
    
    for l in istr:
        l = l.rstrip('~')
        assert type(l)==unicode

        if l.startswith('{{{'):
            os.write(l+'\n')
            for ll in istr:
                os.write(ll+'\n')
                if ll.startswith('}}}'):
                    break
            continue

        if l.startswith(' '):
            istr.push(l)
            parse_quote(istr,os)
            continue

        if l.strip().startswith('----') and l.replace('-',' ').strip()=='':
            os.write('====\n')
            continue

        parse_inline(os,l)
        os.write('\n')

def parse_quote(istr,os):
    os.write('{{{\n')
    for l in istr:
        if l.startswith(' '):
            os.write(l[1:]+'\n')
        else:
            break
    os.write('}}}\n')

wikilabel = re.compile(ur'\[\[([^\]]+)>([\w_/\.\-]+)\]\]',re.U)
namelabel = re.compile(ur'\[\[([^\]]+)>#([_a-zA-Z0-9]+)\]\]',re.U)
areaedit = re.compile(ur'&areaedit\([^\)]*\){([^}]*)};', re.U)
new = re.compile(ur'&new{([^}]*)};', re.U)
pre = re.compile(ur"\[|&",re.U)

def parse_inline(doc, src):
    assert type(src)==unicode
    pos = 0
    while pos<len(src):
        m = pre.search(src,pos)
        if not m:
            doc.write(src[pos:])
            return
        doc.write(src[pos:m.start()])
        pos = m.start()

        if src[pos]=='[':
            m = wikilabel.match(src,pos)
            if m:
                pos += len(m.group(0))
                name = m.group(1)
                url = m.group(2)
                doc.write('[[%s:%s]]'%(name,url))
                continue
            m = namelabel.match(src,pos)
            if m:
                pos += len(m.group(0))
                name = m.group(1)
                url = m.group(2)
                doc.write('[[%s:#%s]]'%(name,url))
                continue
            
        if src[pos]=='&':
            m = areaedit.match(src,pos)
            if m:
                pos += len(m.group(0))
                doc.write(m.group(1))
                continue
            m = new.match(src,pos)
            if m:
                pos += len(m.group(0))
                doc.write(m.group(1))
                continue

        doc.write(src[pos])
        pos += 1
    

class iterdir(object):
    def __init__(self, path, deep=False):
        self._root = path
        self._files = None
        self.deep = deep
    def __iter__(self):
        return self
    def next(self):
        if self._files:
            join = os.path.join
            d = self._files.pop()
            r = join(self._root, d)
            if self.deep and os.path.isdir(r):
                self._files += [join(d,n) for n in os.listdir(r)]
        elif self._files is None:
            self._files = os.listdir(self._root)
        if self._files:
            return self._files[-1]
        else:
            raise StopIteration
                                            
if __name__=='__main__':
    sin  = codecs.getreader('utf-8')(sys.stdin)
    sout = codecs.getwriter('utf-8')(sys.stdout)

    it = iterdir('.',4)
    for x in it:
        p = os.path.basename(x)
        if p == 'body.txt':
            print x
            f = open(x,'r')
            try:
                out = StringIO.StringIO()
                conv(f,out)
                out.seek(0)
                f.close()
                f = open(x, 'w')
                f.write(out.read())

            finally:
                f.close()
