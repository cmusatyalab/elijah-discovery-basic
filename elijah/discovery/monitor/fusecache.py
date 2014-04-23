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
import sys
import errno

from fuse import FUSE, FuseOSError, Operations
from optparse import OptionParser
from Queue import Full


class AccessInfo(object):
    CMD_READ = "read"
    CMD_WRITE = "write"
    CMD_OPEN = "open"
    CMD_CLOSE = "close"

    def __init__(self, cmd, full_path, offset=None, length=None):
        self.inode = os.stat(full_path).st_ino
        self.full_path = full_path
        self.cmd = cmd
        self.offset = offset
        self.length = length

    def __str__(self):
        return "%s(%ld)\t%s" % (self.full_path, self.inode, self.cmd)


class LoopBack(Operations):
    def __init__(self, root, access_queue=None):
        self.root = root
        self.access_queue = access_queue

    def _update(self, access_info):
        if self.access_queue is not None:
            try:
                self.access_queue.put_nowait(access_info)
            except Full:
                pass

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def access(self, path, mode):
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, target, name):
        return os.symlink(self._full_path(target), self._full_path(name))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    def open(self, path, flags):
        full_path = self._full_path(path)
        self._update(AccessInfo(AccessInfo.CMD_OPEN, full_path))
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        self._update(AccessInfo(AccessInfo.CMD_READ, self._full_path(path),
            offset=offset, length=length))
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        self._update(AccessInfo(AccessInfo.CMD_WRITE, self._full_path(path),
            offset=offset, length=len(buf)))
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        self._update(AccessInfo(AccessInfo.CMD_CLOSE, self._full_path(path)))
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def process_command_line(argv):
    VERSION = '0.1'
    DESCRIPTION = 'Looback Fuse layer'

    parser = OptionParser(usage='%prog [mount_point] [loopback] [options]',
            version=VERSION, description=DESCRIPTION)

    parser.add_option(
            '-p', '--pipe', action='store', dest='named_pipe', default=None,
            help="Propagate information to the named pipe")
    settings, args = parser.parse_args(argv)
    if len(args) is not 2:
        parser.error("Need mount point and loopback path")
    mount_point = args[0]
    lookback_path = args[1]
    return mount_point, lookback_path, settings


def main():
    mountpoint, root, settings = process_command_line(sys.argv[1:])
    FUSE(LoopBack(root), mountpoint, foreground=True)


if __name__ == '__main__':
    main()
