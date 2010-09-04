import cgi
import re
import htmlentitydefs

def unescape_charref(ref): 
    name = ref[2:-1] 
    base = 10 
    if name.startswith("x"): 
        name = name[1:] 
        base = 16 
    return unichr(int(name, base)) 
def replace_entities(match): 
    ent = match.group() 
    if ent[1] == "#": 
        return unescape_charref(ent) 
    repl = htmlentitydefs.name2codepoint.get(ent[1:-1]) 
    if repl is not None: 
        repl = unichr(repl) 
    else: 
        repl = ent 
    return repl 

def html_unescape(data): 
    '''
    Unescape (numeric) HTML entities.
    '''
    return re.sub(r"&#?[A-Za-z0-9]+?;", replace_entities, data) 

def html_escape(data):
    '''
    Escape HTML entities.
    '''
    return cgi.escape(data)

