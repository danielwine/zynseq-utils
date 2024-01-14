import logging
from inspect import signature
from core.res.cli_messages import ERR_INVALID, ERR_MISSING_ARG
logger = logging.getLogger()


def get_fn_param_count(func):
    return len(signature(func).parameters.keys())

def decode_params(par):
    if not par:
        return False, False
    comp = par[0]
    lenc = len(comp)
    if lenc < 3 or lenc > 4 or not comp.isnumeric():
        return False, False
    if lenc == 3:
        return int(comp[0]), int(comp[1:3])
    else:
        return int(comp[0:2]), int(comp[2:4])

def decode_pair(par):
    comp1 = par[0]
    comp2 = par[1]
    return decode_params(comp1), decode_params(comp2)

def get_docstrings_for(cls, startswith=''):
    cmds = {}
    for method in cls.__dict__.items():
        if method[0].startswith('_'):
            continue
        if method[0].startswith(startswith):
            cmds[method[0][len(startswith):]] = method[1].__doc__
    return cmds

def convert_params(par, specs):
    ret = []
    for num, typ in enumerate(specs):
        if typ == 'i':
            if par[num].isnumeric():
                ret.append(int(par[num]))
            else:
                # self.print_newline_on(1)
                logger.warning(f'{ERR_INVALID}: numeric')
                return False
        if typ == 'b':
            nm = int(par[num])
            if nm >= 0 and nm < 2:
                ret.append(False if nm == 0 else True)
            else:
                logger.warning(f'{ERR_INVALID}: boolean')
                return False
    return ret

def invoke_mnemo_func(fn, fnparc, p):
    ret = False
    if fnparc == 1:
        ret = fn(p)
    elif fnparc == 2:
        d1, d2 = decode_params(p)
        if d1:
            ret = fn(d1, d2)
    elif fnparc == 4:
        s1, s2, d1, d2 = decode_params(p)
        if s1:
            ret = fn(s1, s2, d1, d2)
    else:
        return
    parst = p if p == '' else ' '.join(x for x in p)
    return ret, parst

def invoke_c_func(fn, specs, p):
    if len(p) < len(specs):
        arg = specs[len(p)]
        logger.warning(f'{ERR_MISSING_ARG}: {arg}')
        return False
    p = convert_params(p, specs)
    if p == None or p == False:
        return False
    lp = len(p)
    if lp == 0:
        r = fn()
    if lp == 1:
        r = fn(p[0])
    elif lp == 2:
        r = fn(p[0], p[1])
    elif lp == 3:
        r = fn(p[0], p[1], p[2])
    elif lp == 4:
        r = fn(p[0], p[1], p[2], p[3])
    elif lp == 5:
        r = fn(p[0], p[1], p[2], p[3], p[4])
    return r
