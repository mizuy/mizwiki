import socket
from mizwiki.misc import memoize

def is_in_rbl(ip, rbl_domain):
    '''
    see
    http://mail.python.org/pipermail/python-list/2000-November/060249.html
    '''
    l = string.split (ip, ".")
    l.reverse ()
    lookup_host = string.join (l, ".") + "." + rbl_domain
    try:
        addr = socket.gethostbyname (lookup_host)
    except socket.error:
        addr = ''
    # Some RBL-like lists use the returned addr to signify something,
    # so we'll return it.
    return addr

class HostValidator(object):
    def __init__(self, rbl, whitelist, blacklist, enable_spamblock, logger=None):
        '''
        rbl: host ip/domains of RBL
        whitelist: host ips for which allow
        blacklist: part of hostname for which reject
        enable_spamblock: True if  rbl-based spamfilter is enabled.
        '''
        self._rbl = rbl
        self._whitelist = whitelist
        self._blacklist = blacklist
        self._spamblock = enable_spamblock
        self.log = logger or (lambda x:None)
    
    @memoize
    def _is_in_whitelist(self, ip):
        return ip in self._whitelist

    @memoize
    def _hostname(self, ip):
        try:
            (hostname,a,b) = socket.gethostbyaddr(ip)
        except socket.error:
            return None
        return hostname

    @memoize
    def _is_in_rbl(self, ip):
        return any(is_in_rbl(ip, rbl) for rbl in self.rbl)

    @memoize
    def _is_in_blacklist(self, ip):
        h = self._hostname(ip)
        return any(h[-len(bl):]==bl for bl in self._blacklist)

    @memoize
    def _has_jp_hostname(self, ip):
        return 'jp' == self._hostname(ip).split('.')[-1]

    # if spam, rejest anyway
    def is_spam(self, ip):
        if not self._spamblock:
            self.log('is_spam(allow): spam block is disabled')
            return False
        if self._is_in__whitelist(ip):
            self.log('is_spam(allow): ip is in whitelist: ip = %s'%ip)
            return False
        if self._is_in_rbl(ip):
            self.log('is_spam(reject): ip is in rbl: ip = %s'%ip)
            return True
        if self._is_in_blacklist(ip):
            h = self._hostname(ip)
            self.log('is_spam(reject): ip is in blacklist: ip=%s hostname=%s'%(ip,self._hostname(ip)))
            return True

        self.log('is_spam(allow): ip is not in rbl or blacklist: ip=%s'%ip)
        return False
    # elif valid_host, allow
    def is_valid_host(self,ip):
        if self._is_in_whitelist(ip):
            self.log('is_valid_host(allow): ip is in whitelist: ip = %s'%ip)
            return True
        if not self._hostname(ip):
            self.log('is_valid_host(reject): ip has no hostname: ip = %s'%ip)
            return False
        if not self._has_jp_hostname(ip):
            self.log('is_valid_host(reject): ip is not in .jp domain: ip=%s, hostname=%s'%(ip,self._hostname(ip)))
            return False

        self.log('is_valid_host(allow): ip has jp domain: ip=%s hostname=%s'%(ip,self._hostname(ip)))
        return True
    # elif valid_answer, allow
    #   disabled.
    # else, retry

