# vz: ViZual language environment
# (c) Dmitry Ponyatov <dponyatov@gmail.com> 2020 All rights reserved

import os, sys

## base object (hyper)graph node
class Object:

    ## @name constructor

    def __init__(self, V):
        self.type = self.tag()
        self.value = V
        self.slot = {}
        self.nest = []

    def box(self, that):
        if isinstance(that, Object): return that
        if isinstance(that, str): return S(that)
        if callable(that): return Cmd(that)
        raise TypeError(['box', type(that), that])

    ## @name text dump

    def __repr__(self): return self.dump()

    def dump(self, cycle=[], depth=0, prefix=''):
        # head
        def pad(depth): return '\n' + '\t' * depth
        ret = pad(depth) + self.head(prefix)
        # slot{}
        for i in self.keys():
            ret += self[i].dump(cycle, depth + 1, f'{i} = ')
        # nest[]ed
        for j, k in enumerate(self):
            ret += k.dump(cycle, depth + 1, f'{j}: ')
        # subtree
        return ret

    def head(self, prefix=''):
        gid = f' @{id(self):x}'
        return f'{prefix}<{self.tag()}:{self.val()}>{gid}'

    def __format__(self, spec=''):
        if not spec: return self.val()
        raise TypeError(['__format__', spec])

    def tag(self): return self.__class__.__name__.lower()
    def val(self): return f'{self.value}'

    ## @name operator

    def keys(self): return sorted(self.slot.keys())

    def __iter__(self): return iter(self.nest)

    def __getitem__(self, key):
        if isinstance(key, str): return self.slot[key]
        raise TypeError(['__getitem__', type(key), key])

    def __setitem__(self, key, that):
        that = self.box(that)
        if isinstance(key, str): self.slot[key] = that; return self
        raise TypeError(['__setitem__', type(key), key, that])

    def __lshift__(self, that):
        that = self.box(that)
        return self.__setitem__(that.tag(), that)

    def __rshift__(self, that):
        that = self.box(that)
        return self.__setitem__(that.val(), that)

    def __floordiv__(self, that):
        self.append(that); return self

    def append(self, that):
        self.nest.append(self.box(that))

    ## @name stack operation

    def dot(self): self.nest.clear(); return self

class Primitive(Object):
    def eval(self, env): env // self

## symbol
class Sym(Primitive):
    def eval(self, env): return env[self.val()].eval(env)

## integer number
class Int(Primitive):
    def __init__(self, N): super().__init__(int(N))

## source code /nested strings/
class S(Primitive):
    def __init__(self, start=None, end=None, pfx=None, sfx=None):
        super().__init__(start)
        self.end = end
        self.pfx = pfx; self.sfx = sfx

    def gen(self, to, depth=0):
        ret = ''
        if self.pfx is not None:
            ret += f'{to.tab*depth}{self.pfx}\n' if self.pfx else '\n'
        if self.value is not None:
            ret += f'{to.tab*depth}{self.value}\n'
        for i in self:
            ret += i.gen(to, depth + 1)
        if self.end:
            ret += f'{to.tab*depth}{self.end}\n'
        if self.sfx is not None:
            ret += f'{to.tab*depth}{self.sfx}\n' if self.sfx else '\n'
        return ret

class Sec(S):
    def gen(self, to, depth=0):
        ret = ''
        if self.nest:
            if self.pfx is not None:
                ret += f'{to.tab*depth}{self.pfx}\n' if self.pfx else '\n'
            if self.value is not None:
                ret += f'{to.tab*depth}{to.comment} \\ {self.value}\n'
            for i in self:
                ret += i.gen(to, depth + 0)
            if self.value is not None:
                ret += f'{to.tab*depth}{to.comment} / {self.value}\n'
        return ret

class IO(Object):
    def __init__(self, V):
        super().__init__(V)
        self.path = V

class Dir(IO):
    def sync(self):
        try: os.mkdir(self.path)
        except FileExistsError: pass
        for i in self: i.sync()

    def __floordiv__(self, that):
        assert isinstance(that, IO)
        that.path = f'{self.path}/{that.path}'
        return super().__floordiv__(that)

class File(IO):
    def __init__(self, V, ext='', tab=' ' * 4, comment='#'):
        super().__init__(V + ext)
        self.ext = ext; self.tab = tab; self.comment = comment
        self.top = Sec(); self.bot = Sec()

    def sync(self):
        with open(self.path, 'w') as F:
            F.write(self.top.gen(self))
            for i in self: F.write(i.gen(self))
            F.write(self.bot.gen(self))

class Meta(Object): pass

class Makefile(File):
    def __init__(self, V='Makefile', ext='', tab='\t', comment='#'):
        super().__init__(V, ext, tab, comment)

class giti(File):
    def __init__(self, V='', ext='.gitignore'):
        super().__init__(V, ext)
        self.bot // f'!{self}'

class jsonFile(File):
    def __init__(self, V, ext='.json', tab=' ' * 4, comment='//'):
        super().__init__(V, ext, tab, comment)

class pyFile(File):
    def __init__(self, V, ext='.py', tab=' ' * 4, comment='#'):
        super().__init__(V, ext, tab, comment)

class mdFile(File):
    def __init__(self, V, ext='.md', tab=' ' * 4, comment='#'):
        super().__init__(V, ext, tab, comment)

class Project(Meta):
    def __init__(self, V=None, title=None):
        if V is None: V = os.getcwd().split('/')[-1]
        super().__init__(V)
        #
        self.TITLE = title if title else self.val()
        self.AUTHOR = 'Dmitry Ponyatov'
        self.EMAIL = 'dponyatov@gmail.com'
        self.YEAR = '2020'
        self.GITHUB = 'https://github.com/ponyatov'
        self.ABOUT = ''
        #
        self.dirs()
        self.mk()
        self.giti()
        self.vscode()
        self.src()

    def copyright(self):
        return \
            f'(c) {self.AUTHOR} <{self.EMAIL}> ' +\
            f'{self.YEAR} All rights reserved'

    def vscode(self):
        self.vscode = Dir('.vscode'); self.d // self.vscode
        self.settings()

    def settings(self):
        self.settings = jsonFile('settings'); self.vscode // self.settings
        self.vsignore = (Sec() // '"vz/**":true,')
        #
        self.exclude = (S('"files.exclude": {', '},')
                        // self.vsignore)
        self.watcher = (S('"files.watcherExclude": {', '},')
                        // self.vsignore)
        self.assoc = (S('"files.associations": {', '},'))
        #
        self.editor = (Sec('editor', pfx='')
                       // '"editor.tabSize": 4,'
                       // '"editor.rulers": [80],'
                       // '"workbench.tree.indent": 32,')
        #
        self.multi = (S('"multiCommand.commands": [', '],'))

        def multi(key, cmd):
            return (S('{', '},')
                    // f'"command": "multiCommand.{key}",'
                    // (S('"sequence": [', ']')
                        // '"workbench.action.files.saveAll",'
                        // (S('{"command": "workbench.action.terminal.sendSequence",')
                        // f'"args": {{"text": "{cmd}"}}}}')
                        )
                    )
        for i, j in [
                ['f11', '\\u000D make repl \\u000D'],
                ['f12', 'sys.exit(0)\\u000D']
        ]:
            self.multi // multi(i, j)
        #
        self.settings \
            // (S('{', '}')
                // self.multi
                // (Sec('files', pfx='')
                    // self.exclude
                    // self.watcher
                    // self.assoc)
                // self.editor)

    def src(self):
        self.py = pyFile(f'{self}'); self.d // self.py
        self.py \
            // (Sec(sfx='')
                // f'# {self}: {self.TITLE}'
                // f'# {self.copyright()}'
                )
        self.py \
            // (S('import os, sys', pfx=''))
        self.py \
            // (Sec(pfx='')
                // f"p = Project(title='{self.TITLE}')"
                )
        #
        self.test = pyFile(f'test_{self}'); self.d // self.test
        self.test // 'import pytest' // f'from {self} import *'
        self.test // (S('def test_any(): assert True', pfx='', sfx=''))

    def dirs(self):
        self.d = Dir(f'{self}')
        self.d.bin = Dir('bin'); self.d // self.d.bin
        self.d.bin // (giti() // '*')
        self.d.doc = Dir('doc'); self.d // self.d.doc
        self.d.doc // (giti() // '*.pdf')
        self.d.lib = Dir('lib'); self.d // self.d.lib
        self.d.lib // giti()
        self.d.src = Dir('src'); self.d // self.d.src
        self.d.src // giti()
        self.d.tmp = Dir('tmp'); self.d // self.d.tmp
        self.d.tmp // (giti() // '*')

    def giti(self):
        self.giti = giti(); self.d // self.giti
        self.giti.top // '*~' // '*.swp' // '*.log'
        self.giti // f'/{self}/'

    def mk(self):
        self.mk = Makefile(); self.d // self.mk
        #
        self.mk.var = Sec('var'); self.mk // self.mk.var
        self.mk.var \
            // f'MODULE = $(notdir $(CURDIR))'
        #
        self.mk.tool = (Sec('tool', pfx='')
                        // 'CURL = curl -L -o'
                        // 'PY   = $(shell which python3)'
                        // 'PEP  = $(shell which autopep8)'
                        // 'PEPS = E26,E302,E305,E401,E402,E701,E702'
                        )
        self.mk // self.mk.tool
        #
        self.mk.src = Sec('src', pfx=''); self.mk // self.mk.src
        self.mk.src // 'SRC = $(MODULE).py'
        #
        self.mk.all = Sec('all', pfx=''); self.mk // self.mk.all
        self.mk.all \
            // (S('repl: $(SRC)')
                // '$(PY) -i $<'
                // '$(PEP) --ignore=$(PEPS) --in-place $?'
                // '$(MAKE) $@')
        #
        self.mk.doc_ = Sec('doc', pfx='')
        self.mk.doc = S('doc:', pfx='\n.PHONY: doc')
        self.mk // (self.mk.doc_ // self.mk.doc)

    def readme(self):
        self.readme = mdFile('README'); self.d // self.readme
        self.readme \
            // f'#  ![logo](doc/logo.png) `{self}`' \
            // f'## {self.TITLE}' // '' // self.copyright() // '' \
            // 'github: {self.GITHUB}/{self}' // '' // self.ABOUT

    def sync(self):
        self.readme()
        self.d.sync()

class Net(Object): pass

class URL(Net): pass


p = Project(title='ViZual language environment')

p.mk.doc.value += ' doc/diva2.pdf'
p.mk.doc_ \
    // (S('doc/diva2.pdf:')
        // '$(CURL) $@ http://www.diva-portal.org/smash/get/diva2:22296/FULLTEXT01.pdf')

p.sync()

class Container(Object): pass

class Stack(Container): pass

class Map(Container): pass

class Vector(Container): pass

class Queue(Container): pass

class Active(Object): pass

class Env(Active, Map): pass

glob = Env('global')

class Cmd(Active):
    def __init__(self, F):
        assert callable(F)
        super().__init__(F.__name__)
        self.fn = F

    def eval(self, env):
        self.fn(env)

glob['sys'] = lambda env: os._exit(0)
glob['.'] = lambda env: env.dot()
glob['exit'] = lambda env: None
glob['('] = lambda env: None
glob[')'] = lambda env: None

import ply.lex as lex

tokens = ['sym', 'int']

t_ignore = ' \t\r'
t_ignore_comment = '\#.*'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_int(t):
    r'[+\-]?[0-9]+'
    return Int(t.value)

def t_sym(t):
    r'[a-zA-Z0-9_]+|[.()]'
    return Sym(t.value)

def t_error(t): raise SyntaxError(t)

lexer = lex.lex()

def REPL():
    while True:
        print(glob)
        print('-' * 66)
        lexer.input(input('> '))
        while True:
            token = lexer.token()
            if not token: break
            print(token)
            token.eval(glob)
        print(glob)

if __name__ == '__main__':
    REPL()
