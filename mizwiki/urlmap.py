import re

class UrlMap:
    class Rule:
        def __init__(self, name, c, re_rule, gen, var):
            self.name = name
            self.controller = c
            self.re = re.compile(re_rule,re.U)
            self.gen = gen or re_rule.rstrip('$').lstrip('^')
            self.var = var
    def __init__(self):
        self._rulelist = []
        self._rules = {}

    def add_rule(self, name, controller, re_rule, generator=None, variables={}):
        r = self.Rule(name, controller, re_rule, generator, variables)
        self._rulelist.append(r)
        self._rules[name] = r

    def dispatch(self, upath_info, error=None):
        '''
        TODO: big unified regex. (faster?)
        '''
        for r in self._rulelist:
            m = r.re.match(upath_info)
            if m:
                vars = {}
                for i,var in enumerate(r.var):
                    vars[var] = m.group(i+1)
                if error:
                    error('controller=%s, vars=%s'%(r.controller.__class__.__name__,vars))
                return lambda ri:r.controller(ri, **vars)
        return None

    def url_for(self, name, **variables):
        r = self._rules[name]
        assert len(variables)==len(r.var)
        assert all(variables.has_key(var) for var in r.var)
        return r.gen % tuple([variables[var] for var in r.var])
