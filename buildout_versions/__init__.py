# Copyright (c) 2010 Simplistix Ltd
# See license.txt for license details.

import os
import pkg_resources

from datetime import datetime
from zc.buildout import easy_install
from zc.buildout.easy_install import Installer

required_by = {}
picked_versions = {}

# code to patch in
def _log_requirement(ws, req):
    for dist in sorted(ws):
        if req in dist.requires():
            req_ = str(req)
            if req_ not in required_by:
                required_by[req_] = set()
            required_by[req_].add(str(dist.as_requirement()))

original_get_dist = Installer._get_dist
def _get_dist(self, requirement, ws, always_unzip):
    dists = original_get_dist(self, requirement, ws, always_unzip)
    for dist in dists:
        if not (dist.precedence == pkg_resources.DEVELOP_DIST or \
                  (len(requirement.specs) == 1 and \
                       requirement.specs[0][0] == '==')):
            picked_versions[dist.project_name] = dist.version
    return dists

file_name = None

def start(buildout):
    global file_name
    easy_install._log_requirement = _log_requirement
    Installer._get_dist = _get_dist
    if 'buildout_versions_file' in buildout['buildout']:
        file_name = buildout['buildout']['buildout_versions_file']
    
def finish(buildout):
    if picked_versions:
        output = ['[versions]']
        for dist_, version in sorted(picked_versions.items()):
            if dist_ in required_by:
                output.append('# Required by:')
                for req_ in sorted(required_by[dist_]):
                    output.append('# '+req_)
            output.append("%s = %s" % (dist_, version))

        print "Versions had to be automatically picked."
        print "The following part definition lists the versions picked:"
        print '\n'.join(output)
        if file_name:
            if os.path.exists(file_name):
                output[:1] = [
                    '',
                    '# Added by Buildout Versions at %s' % datetime.now(),
                    ]
            output.append('')
            f = open(file_name,'a')
            f.write('\n'.join(output))
            f.close()
            print "This information has been written to %r" % file_name

