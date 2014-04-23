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
import threading
from multiprocessing import Queue
import multiprocessing
import time
import sys

from fuse import FUSE, FuseOSError, Operations
from optparse import OptionParser
from Queue import Empty
from fusecache import LoopBack
from fusecache import AccessInfo

from ..config import DiscoveryConst as DiscoveryConst
from ..log import logging


LOG = logging.getLogger(__name__)


_cache_monitor_instance = None
_fuse_instance = None


def get_instance():
    global _cache_monitor_instance
    global _fuse_instance

    if _cache_monitor_instance is None:
        LOG.info("[CACHE] FUSE mount at %s, which is loop back of %s" % \
                (DiscoveryConst.CLOUDLET_FS_ROOT, DiscoveryConst.DFS_ROOT))
        access_queue = Queue()
        _fuse_instance = FuseLauncher(DiscoveryConst.CLOUDLET_FS_ROOT,\
                DiscoveryConst.DFS_ROOT, access_queue)
        _fuse_instance.start()
        LOG.info("[CACHE] start Cache monitoring")
        _cache_monitor_instance = _CacheMonitor(access_queue,\
                DiscoveryConst.DFS_ROOT, print_out=False)
        _cache_monitor_instance.start()
    return _cache_monitor_instance


def terminate():
    global _cache_monitor_instance
    global _fuse_instance
    
    if _cache_monitor_instance is not None:
        _cache_monitor_instance.terminate()
        _cache_monitor_instance = None
    if _fuse_instance is not None:
        _fuse_instance.terminate()
        _fuse_instance = None


class CacheMonitorError(Exception):
    pass


class _CacheMonitor(threading.Thread):
    def __init__(self, access_queue, dfs_root, print_out=False):
        self.access_queue = access_queue
        self.dfs_root = dfs_root
        self.print_out = print_out
        self.stop = threading.Event()
        self.cache_info_dict = dict() # inode:cache_status
        threading.Thread.__init__(self, target=self.process)

    def process(self):
        while (self.stop.wait(0.01) is False):
            try:
                access = self.access_queue.get_nowait()
                if access.cmd == AccessInfo.CMD_READ or \
                        access.cmd == AccessInfo.CMD_WRITE:
                    self.cache_info_dict[access.inode] = access
                if self.print_out is True:
                    print access
            except Empty:
                continue

    def cached_files(self):
        file_list = list()
        for (inode, access) in self.cache_info_dict.iteritems():
            relpath = os.path.relpath(access.full_path, self.dfs_root)
            file_list.append(relpath)

        file_list.sort()
        return file_list

    def check_file(self, filename, is_abspath=False):
        if is_abspath is True:
            abspath = filename
        else:
            abspath = os.path.join(self.dfs_root, filename)

        if os.path.exists(abspath) is False:
            return False
        else:
            inode = os.stat(abspath).st_ino
            access_info = self.cache_info_dict.get(inode, None)
            if access_info is not None:
                return True
            else:
                return False

    def terminate(self):
        LOG.info("get signal")
        self.stop.set()


class CmdInterface(threading.Thread):
    def __init__(self, cache_monitor):
        self.cache_monitor = cache_monitor
        threading.Thread.__init__(self, target=self.run)

    def run(self):
        while True:
            user_input = raw_input("> ").lower().strip()
            
            if user_input == "list":
                print "\n".join(self.cache_monitor.cached_files())
            elif len(user_input) == 0:
                continue
            elif user_input == 'q':
                break
            else:
                print "Invalid command"

    def terminate(self):
        pass



class FuseLauncher(multiprocessing.Process):
    def __init__(self, mountpoint, root, access_queue):
        self.stop = threading.Event()
        self.mountpoint = mountpoint
        self.root = root
        self.access_queue = access_queue
        if os.path.isdir(self.root) is False or\
                os.access(self.root, os.R_OK | os.W_OK) is False:
            msg = "Failed to setup cache monitoring at %s\n" % self.root
            msg += "Please create a directory for the distributed file system at %s\n" %\
                    self.root
            msg += "Or you can change path to the directory at\n"
            msg += "elijah-discovery/elijah/discovery/Const.py, DFS_ROOT variable"
            raise CacheMonitorError(msg)
        if os.path.isdir(self.mountpoint) is False or\
                os.access(self.mountpoint, os.R_OK | os.W_OK) is False:
            msg = "Failed to setup cache monitoring at %s\n" % self.mountpoint
            msg += "Please create a directory for the loopback at %s\n" %\
                    self.mountpoint
            msg += "Or you can change path to the directory at\n"
            msg += "elijah-discovery/elijah/discovery/Const.py, "
            msg += "CLOUDLET_FS_ROOT variable"
            raise CacheMonitorError(msg)
        multiprocessing.Process.__init__(self)

    def run(self):
        FUSE(LoopBack(self.root, self.access_queue), self.mountpoint, foreground=True)

    def terminate(self):
        self.stop.set()


def process_command_line(argv):
    VERSION = '0.1'
    DESCRIPTION = 'Cache monitor'

    parser = OptionParser(usage='%prog [mount_point] [root] [options]',
            version=VERSION, description=DESCRIPTION)
    parser.add_option(
            '-v', '--verbose', action='store_true', dest='print_console', default=False,
            help="print out access info in realtime")

    settings, args = parser.parse_args(argv)
    if len(args) is not 2:
        parser.error("Need mount point and root path")
    mount_point = args[0]
    lookback_path = args[1]
    return mount_point, lookback_path, settings


def main():
    mountpoint, root, settings = process_command_line(sys.argv[1:])

    access_queue = Queue()
    fuse = FuseLauncher(mountpoint, root, access_queue)
    cache_monitor = _CacheMonitor(access_queue, settings.print_console)
    cmdline_interface = None
    if not settings.print_console:
        cmdline_interface = CmdInterface(cache_monitor)
        cmdline_interface.start()

    fuse.start()
    cache_monitor.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        print "User interrupt"
        ret_code = 1
    finally:
        if cache_monitor is not None:
            cache_monitor.terminate()
        if fuse is not None:
            fuse.terminate()
        if cmdline_interface is not None:
            cmdline_interface.terminate()


if __name__ == '__main__':
    main()
