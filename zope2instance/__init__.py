# Copyright (c) 2010 Simplistix Ltd
# See license.txt for license details.

import cStringIO
import os
import zc.recipe.egg
import zc.buildout

from ZConfig import ConfigurationSyntaxError,schemaless

#[buildout]
#parts = instance
#extends = http://download.zope.org/Zope2/index/<Zope version>/versions.cfg

#[instance]
#recipe = zc.recipe.egg
#eggs = Zope2
#interpreter = py
#scripts = runzope zopectl
#initialization =
#import sys
#  sys.argv[1:1] = ['-C',r'${buildout:directory}/etc/zope.conf']


class Instance:

    def __init__(self, buildout, name, options):
        self.name, self.options = options.get('name', name), options
        self.deployment = deployment = options['deployment']
        options['deployment-name'] = buildout[deployment].get('name', deployment)
        # directories
        options['rc-directory'] = buildout[deployment]['rc-directory']
        options['run-directory'] = buildout[deployment]['run-directory']
        options['etc-directory'] = buildout[deployment]['etc-directory']
        # eggs
        options['eggs'] = options.get('eggs','') + '\nZope2'
        options['scripts'] = 'runzope zopectl'
        self.egg = zc.recipe.egg.Egg(buildout, name, options)

    def _created(self,name,prefix=None):
        path = os.path.join(
            prefix or self.options['rc-directory'],
            self.options['deployment-name']+'-'+self.name+'-'+name,
            )
        self.options.created(path)
        return path
        
    def install(self):
        options = self.options
        zope_conf = options.get('zope.conf', '')+'\n'
        try:
            config = schemaless.loadConfigFile(
                cStringIO.StringIO(zope_conf)
                )
        except ConfigurationSyntaxError,e:
            raise zc.buildout.UserError(
                '%s in:\n%s' % (e,zope_conf)
                )

        zope_conf_path = self._created('zope.conf',options['etc-directory'])
        open(zope_conf_path, 'w').write(str(zope_conf))

        interpreter_path = self._created('py')
        program_path = self._created('runzope')
        
        kw = dict(
            )

        requirements, working_set = self.egg.working_set()

        # zopectl + py
        zc.buildout.easy_install.scripts(
            requirements, working_set,
            options['executable'],
            options['rc-directory'],
            scripts=dict(zopectl=self._created('zopectl')),
            interpreter=interpreter_path,
            initialization="""
import os,sys
os.environ['PYTHON'] = %r
sys.argv[1:1] = ['-C',%r]

# monkey patch annoyance
from Zope2.Startup.zopectl import ZopeCtlOptions

def __setattr__(self,name,value):
    if name!='program':
        self.__dict__[name]=value

ZopeCtlOptions.program = [%r]
ZopeCtlOptions.__setattr__ = __setattr__

""" % (
                interpreter_path,
                zope_conf_path,
                program_path,
            ))

        # runzope
        zc.buildout.easy_install.scripts(
            requirements, working_set,
            options['executable'],
            options['rc-directory'],
            scripts=dict(runzope=program_path),
            initialization="""
import os,sys
os.environ['PYTHON'] = %r
sys.argv[1:1] = ['-C',%r]
""" % (
                interpreter_path,
                zope_conf_path,
            ))
        
        return options.created()

    update = install
