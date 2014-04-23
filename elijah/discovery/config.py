#!/usr/bin/env python 
#
# Cloudlet Infrastructure for Mobile Computing
#
#   Author: Kiryong Ha <krha@cmu.edu>
#
#   Copyright (C) 2011-2013 Carnegie Mellon University
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import os


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK) 
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return exe_file


class CLOUDLET_FEATURE(object):
    VM_SYNTHESIS_APP        = "vm-synthesis-app"
    VM_SYNTHESIS_OPENSTACK  = "vm-synthesis-openstack"
    VM_SYNTHESIS_VMNETX     = "vmnetx"


class DiscoveryConst(object):
    VERSION         = "0.4.0"
    LOG_PATH        = "/var/tmp/cloudlet/log-discovery"

    # Cloudlet registration
    REGISTER_URL        = "/api/v1/Cloudlet/"
    REST_API_PORT       = 8022
    REST_API_URL        = "/api/v1/resource/"
    KEY_REST_PORT   = "rest_api_port"
    KEY_REST_URL    = "rest_api_url"
    KEY_FEATURES    = "features"
    KEY_CLOUDLET_IP = "ip_address"
    KEY_LATITUDE    = "latitude"
    KEY_LONGITUDE   = "longitude"


    # Cloudlet Storage
    CLOUDLET_FS_ROOT = "/cloudletFS"
    DFS_ROOT = "/magfs/home/kiryongh/"

    # Avahi server
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    SERVICE_NAME = "cloudlet service"
    SERVICE_PORT = REST_API_PORT

    # HTTP cache proxy monitor
    SQUID_LOG_FILE = "/var/log/squid3/store.log"


