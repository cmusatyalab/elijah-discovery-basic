#!/usr/bin/env python 
#
# cloudlet infrastructure for mobile computing
#
#   author: kiryong ha <krha@cmu.edu>
#
#   copyright (c) 2011-2014 Carnegie Mellon University
#   licensed under the apache license, version 2.0 (the "license");
#   you may not use this file except in compliance with the license.
#   you may obtain a copy of the license at
#
#       http://www.apache.org/licenses/license-2.0
#
#   unless required by applicable law or agreed to in writing, software
#   distributed under the license is distributed on an "as is" basis,
#   without warranties or conditions of any kind, either express or implied.  
#   see the license for the specific language governing permissions and
#   limitations under the license.
#

import os
import sys
from elijah.discovery.config import DiscoveryConst as Const

#from setuptools import setup, find_packages
from distutils.core import setup

# get all executable file 
def get_all_files(package_dir, target_path, exclude_names=list()):
    data_files = list()
    cur_dir = os.path.abspath(os.curdir)
    os.chdir(package_dir)
    for (dirpath, dirnames, filenames) in os.walk(target_path):
        for filename in filenames:
            if filename.startswith('.') == True:
                continue
            if filename in exclude_names:
                continue
            data_files.append(os.path.join(dirpath, filename))
    os.chdir(cur_dir)
    return data_files

script_files = get_all_files(".", "bin")

setup(
        name='elijah-discovery',
        version=str(Const.VERSION),
        description='Cloudlet registration and discovery',
        long_description=open('README.md', 'r').read(),
        url='https://github.com/cmusatyalab/elijah-discovery/',

        author='Kiryong Ha',
        author_email='krha@cmu.edu',
        keywords="cloud cloudlet discovery cmu",
        license='Apache License Version 2.0',
        scripts=script_files,
        packages=[
            'elijah',
            'elijah.discovery',
            'elijah.discovery.client',
            'elijah.discovery.monitor',
            ],
        data_files=[],
        requires=[],
        #classifier=[
        #    'Development Status :: 3 - Alpha',
        #    'License :: OSI Approved :: Apache Software License',
        #    'Operating System :: POSIX :: Linux',
        #],
        )


