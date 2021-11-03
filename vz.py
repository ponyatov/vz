import os, sys

class Object:

    ## @name constructor

    def __init__(self, V):
        self.value = V
        self.nest = []

    def box(self, that):
        if isinstance(that, Object): return that
        if isinstance(that, str): return S(that)
        raise TypeError(['box', type(that), that])

    ## @name dump / string

    def test(self): return self.dump(test=True)
    def __repr__(self): return self.dump(test=False)

    def dump(self, cycle=[], depth=0, prefix='', test=False):
        # head
        def pad(depth): return '\n' + '\t' * depth
        ret = pad(depth) + self.head(prefix, test)
        # subtree
        return ret

    def head(self, prefix='', test=False):
        gid = '' if test else f' @{id(self):x}'
        return f'{prefix}<{self.tag()}:{self.val()}>{gid}'

    def __format__(self, spec=''):
        if not spec: return self.val()
        raise TypeError(['__format__', spec])

    def tag(self): return self.__class__.__name__.lower()
    def val(self): return f'{self.value}'

    ## @name operator

    def __iter__(self):
        return iter(self.nest)

    def __floordiv__(self, that):
        self.nest.append(self.box(that)); return self

class Primitive(Object):
    pass

class S(Primitive):
    def __init__(self, V=None, end=None, pfx=None, sfx=None):
        super().__init__(V)
        self.end = end; self.pfx = pfx; self.sfx = sfx

    def gen(self, to, depth=0):
        ret = ''
        if self.pfx is not None:
            ret += f'{to.tab*depth}{self.pfx}\n'
        if self.value is not None:
            ret += f'{to.tab*depth}{self.value}\n'
        for i in self:
            ret += i.gen(to, depth + 1)
        if self.end is not None:
            ret += f'{to.tab*depth}{self.end}\n'
        if self.sfx is not None:
            ret += f'{to.tab*depth}{self.sfx}\n'
        return ret

class Sec(S):
    def gen(self, to, depth=0):
        ret = ''
        if self.pfx is not None:
            ret += f'{to.tab*depth}{self.pfx}\n' if self.pfx else '\n'
        if self.nest and self.value is not None:
            ret += f'{to.tab*depth}{to.comment} \\ {self}\n'
        for i in self:
            ret += i.gen(to, depth + 0)
        if self.nest and self.value is not None:
            ret += f'{to.tab*depth}{to.comment} / {self}\n'
        if self.sfx is not None:
            ret += f'{to.tab*depth}{self.sfx}\n' if self.pfx else '\n'
        return ret

class IO(Object):
    def __init__(self, V):
        super().__init__(V)
        self.path = V

class Dir(IO):
    def __floordiv__(self, that):
        assert isinstance(that, IO)
        that.path = f'{self.path}/{that.path}'
        return super().__floordiv__(that)

    def sync(self):
        try: os.mkdir(self.path)
        except FileExistsError: pass
        for i in self: i.sync()

class File(IO):
    def __init__(self, V, ext='', tab=' ' * 4, comment='#'):
        super().__init__(V + ext)
        self.top = Sec(); self.bot = Sec()
        self.tab = tab; self.comment = comment

    def sync(self):
        with open(self.path, 'w') as F:
            F.write(self.top.gen(self))
            for i in self: F.write(i.gen(self))
            F.write(self.bot.gen(self))

class giti(File):
    def __init__(self, V='.gitignore'):
        super().__init__(V)
        self.bot // f'!{self}'

class Makefile(File):
    def __init__(self, V='Makefile'):
        super().__init__(V, tab='\t')

class pyFile(File):
    def __init__(self, V, ext='.py'):
        super().__init__(V, ext)

class jsonFile(File):
    def __init__(self, V, ext='.json', comment='//'):
        super().__init__(V, ext, comment=comment)

class Meta(Object): pass

class Class(Meta):
    def __init__(self, C, sup=[]):
        assert callable(C)
        super().__init__(C.__name__)
        self.clazz = C; self.sup = sup

    def gen(self, to, depth=0):
        ret = S(f'class {self}:', pfx='') // 'pass'
        return ret.gen(to, depth)

class Project(Meta):
    def __init__(self, V=None, title='', about=''):
        if not V: V = os.getcwd().split('/')[-1]
        super().__init__(V)
        #
        self.TITLE = title if title else f'{self}'
        self.ABOUT = about
        self.AUTHOR = 'Dmitry Ponyatov'
        self.EMAIL = 'dponyatov@gmail.com'
        self.GITHUB = 'https://github.com/ponyatov'
        self.YEAR = 2020
        self.LICENSE = 'All rights reserved'
        self.COPYRIGHT = f'(c) {self.AUTHOR} <{self.EMAIL}> {self.YEAR} {self.LICENSE}'
        #
        self.dirs()
        self.mk()
        self.src()
        self.vscode()
        self.apt()

    def apt(self):
        self.apt = File('apt', '.txt'); self.d // self.apt
        self.apt \
            // 'git make curl' // 'code meld' \
            // 'python3 python3-venv' \
            // 'build-essential g++'

    def vscode(self):
        self.vscode = Dir('.vscode'); self.d // self.vscode
        self.settings()
        self.tasks()

    def settings(self):
        self.settings = jsonFile('settings'); self.vscode // self.settings
        #

        def multi(key, cmd):
            return (S('{', '},')
                    // f'"command": "multiCommand.{key}",'
                    // (S('"sequence": [', ']')
                    // '"workbench.action.files.saveAll",'
                    // (S('{"command": "workbench.action.terminal.sendSequence",')
                        // f'"args": {{"text": "\\u000D {cmd} \\u000D"}}}}'
                        )))
        self.multi = \
            (Sec('multi')
             // (S('"multiCommand.commands": [', '],')
                 // multi('f11', 'make meta')
                 // multi('f12', 'make all')
                 ))
        #
        self.files = (Sec()
                      // f'"{self}/**":true,'
                      )
        self.exclude = \
            (Sec()
             // (S('"files.exclude": {', '},') // self.files))
        self.watcher = \
            (Sec()
             // (S('"files.watcherExclude": {', '},') // self.files))
        self.assoc = \
            (Sec()
             // (S('"files.associations": {', '},')))
        self.files = (Sec('files', pfx='')
                      // self.exclude
                      // self.watcher
                      // self.assoc)
        #
        self.editor = (Sec('editor', pfx='')
                       // '"editor.tabSize": 4,'
                       // '"editor.rulers": [80],'
                       // '"workbench.tree.indent": 32,'
                       )
        #
        self.settings \
            // (S('{', '}')
                // self.multi
                // self.files
                // self.editor)

    def tasks(self):
        self.tasks = jsonFile('tasks'); self.vscode // self.tasks

        def task(clazz, cmd):
            return (S('{', '},')
                    // f'"label":          "{clazz}: {cmd}",'
                    // f'"type":           "shell",'
                    // f'"command":        "make {cmd}",'
                    // f'"problemMatcher": []'
                    )
        self.tasks \
            // (S('{', '}')
                // '"version": "2.0.0",'
                // (S('"tasks": [', ']')
                    // task('project', 'install')
                    // task('project', 'update')
                    // task('git', 'dev')
                    // task('git', 'shadow')
                    ))

    def src(self):
        self.py()
        self.test()
        self.config()

    def config(self):
        self.config = pyFile('config'); self.d // self.config
        self.config \
            // f"{'SECURE_KEY':<11} = {os.urandom(0x22)}" \
            // f"{'HOST':<11} = '127..0.0.1'" \
            // f"{'PORT':<11} = 12345"

    def py(self):
        self.py = pyFile(f'{self}'); self.d // self.py
        self.py \
            // 'import os, sys'
        for i in [Object, S, Sec, IO, Dir, File, Meta, Class, Project]:
            self.py // Class(i)
        self.py // Class(Primitive, [Object])
        self.py \
            // S('Project().sync()', pfx='')

    def test(self):
        self.test = pyFile(f'test_{self}'); self.d // self.test
        self.test \
            // 'import pytest' \
            // f'from {self} import *' \
            // 'def test_any(): assert True'

    def dirs(self):
        self.d = Dir(f'{self}'); self.giti = giti(); self.d // self.giti
        self.giti.top // '*~' // '*.swp' // '*.log'; self.giti.top.sfx = ''
        self.giti // f'/{self}/' // '/__pycache__/'
        self.giti.bot.pfx = ''
        #
        self.bin = Dir('bin'); self.d // self.bin

    def mk(self):
        self.mk = Makefile(); self.d // self.mk
        #
        self.mk.var = Sec('var', pfx=''); self.mk // self.mk.var
        self.mk.var \
            // f'{"MODULE":<11} = $(notdir $(CURDIR))' \
            // f'{"OS":<11} = $(shell uname -s)' \
            // f'{"CORES":<11} = $(shell grep processor /proc/cpuinfo | wc -l)'
        #
        self.mk.dir = Sec('dir', pfx=''); self.mk // self.mk.dir
        self.mk.dir \
            // f'{"CWD":<11} = $(CURDIR)' \
            // f'{"BIN":<11} = $(CWD)/bin' \
            // f'{"DOC":<11} = $(CWD)/doc' \
            // f'{"LIB":<11} = $(CWD)/lib' \
            // f'{"SRC":<11} = $(CWD)/src' \
            // f'{"TMP":<11} = $(CWD)/tmp'
        #
        self.mk.tool = Sec('tool', pfx=''); self.mk // self.mk.tool
        self.mk.tool \
            // f'CURL = curl -L -o' \
            // f'PY   = $(shell which python3)' \
            // f'PYT  = $(shell which pytest)' \
            // f'PEP  = $(shell which autopep8)'
        #
        self.mk.package = Sec('package', pfx=''); self.mk // self.mk.package
        self.mk.package \
            // f'SYSLINUX_VER = 6.0.3'
        #
        self.mk.src = Sec('src', pfx=''); self.mk // self.mk.src
        self.mk.src \
            // f'Y += $(MODULE).py test_$(MODULE).py' \
            // f'P += config.py' \
            // f'S += $(Y)'
        #
        self.mk.cfg = Sec('cfg', pfx=''); self.mk // self.mk.cfg
        self.mk.cfg \
            // f'PEPS = E26,E302,E305,E401,E402,E701,E702'
        #
        self.mk.all = Sec('all', pfx=''); self.mk // self.mk.all
        self.mk.all \
            // (S('meta: $(Y)', pfx='.PHONY: meta')
                // '$(MAKE) test'
                // '$(PY)   $(MODULE).py'
                // '$(PEP)  --ignore=$(PEPS) --in-place $?')
        self.mk.all \
            // (S('test: $(Y)', pfx='\n.PHONY: test')
                // '$(PYT) test_$(MODULE).py')
        #
        self.mk.rule = Sec('rule', pfx=''); self.mk // self.mk.rule
        #
        self.mk.doc = Sec('doc', pfx=''); self.mk // self.mk.doc
        self.mk.doc \
            // S('doc: doc/pyMorphic.pdf', pfx='.PHONY: doc')
        self.mk.doc \
            // (S('doc/pyMorphic.pdf:')
                // '$(CURL) $@ http://www.diva-portal.org/smash/get/diva2:22296/FULLTEXT01.pdf')
        #
        self.mk.install = Sec('install', pfx=''); self.mk // self.mk.install
        self.mk.install // '.PHONY: install update'
        self.mk.install \
            // (S('install: $(OS)_install doc')
                // '$(MAKE) test'
                )
        self.mk.install \
            // (S('update: $(OS)_update doc')
                // '$(MAKE) test'
                )
        self.mk.install \
            // (S('Linux_install Linux_update:',
                  pfx='.PHONY: Linux_install Linux_update')
                // 'sudo apt update'
                // 'sudo apt install -u `cat apt.txt`')
        #
        self.mk.merge = Sec('merge', pfx=''); self.mk // self.mk.merge
        self.mk.merge \
            // 'SHADOW ?= ponymuck'
        self.mk.merge \
            // 'MERGE   = Makefile .gitignore README.md apt.txt $(S)' \
            // 'MERGE  += .vscode bin doc lib src tmp'
        self.mk.merge \
            // (S('dev:', pfx='\n.PHONY: dev')
                // 'git push -v'
                // 'git checkout $@'
                // 'git checkout $(SHADOW) -- $(MERGE)'
                )
        self.mk.merge \
            // (S('shadow:', pfx='\n.PHONY: shadow')
                // 'git push -v'
                // 'git checkout $(SHADOW)'
                )
        self.mk.merge \
            // (S('release:', pfx='\n.PHONY: release')
                )
        self.mk.merge \
            // (S('zip:', pfx='\n.PHONY: zip')
                )

    def sync(self):
        self.readme()
        self.d.sync()

    def readme(self):
        self.readme = File('README', '.md'); self.d // self.readme
        self.readme \
            // f'#  ![logo](doc/logo.png) `{self}`' // f'## {self.TITLE}'
        self.readme \
            // '' // self.COPYRIGHT // '' // f'github: {self.GITHUB}/{self}'
        self.readme // self.ABOUT
Project(
    title='ViZual language environment',
    about='''
* object (hyper)graph interpreter
'''
).sync()
