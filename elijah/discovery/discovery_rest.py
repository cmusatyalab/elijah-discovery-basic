#!/usr/bin/env python

import os
import sys
import json
import fnmatch
import glob2

from flask import Flask
from flask import request
from flask.ext import restful
from flask.ext.restful import Resource
from flask import jsonify
from monitor.resource import ResourceMonitor
from monitor import file_cache
import log as logging

from config import DiscoveryConst
from monitor import ResourceConst
from client.app_info import AppInfo


class TmpLogging(object):
    def __init__(self):
        self.out = sys.stdout
        self.err = sys.stderr

    def info(self, msg):
        self.out.write("INFO\t%s\n" % msg)
        self.out.flush()

    def debug(self, msg):
        self.out.write("DEBUG\t%s\n" % msg)
        self.out.flush()

    def error(self, msg):
        self.err.write("ERROR\t%s\n" % msg)
        self.out.flush()

# Flaks intercept logging class, so we temporarily 
# use own class to print log message
LOG = TmpLogging()


class ResourceInfo(Resource):
    resource_monitor = None
    file_cache_monitor = None

    def __init__(self, *args, **kwargs):
        super(ResourceInfo, self).__init__(*args, **kwargs)
        if self.resource_monitor is None:
            self.resource_monitor = ResourceMonitor()
        try:
            if self.file_cache_monitor is None:
                self.file_cache_monitor = file_cache.get_instance()
        except file_cache.CacheMonitorError as e:
            self.file_cache_monitor = None
        self.dfs_root = DiscoveryConst.DFS_ROOT

    def get(self):
        ret_data = self.resource_monitor.get_static_resource()
        ret_data.update(self.resource_monitor.get_dynamic_resource())

        request_opts = request.json or None
        if request_opts is not None and \
                AppInfo.APPLICATION in request_opts:
            app_info = request_opts.get(AppInfo.APPLICATION)
            app_id = app_info.get(AppInfo.APP_ID, None)

            # file cache
            cache_files = list()
            cache_score = float(0)
            if self.file_cache_monitor is not None:
                file_cachelist = app_info.get(AppInfo.REQUIRED_CACHE_FILES, None)
                cache_files, total_filesize, total_cachesize = \
                        self.check_file_cache(file_cachelist)
                if total_filesize is not 0:
                    cache_score = float(100.0*total_cachesize/total_filesize)
                else:
                    cache_score = float(0)
            ret_data.update({\
                    ResourceConst.APP_CACHE_FILES: cache_files,
                    ResourceConst.APP_CACHE_TOTAL_SCORE: cache_score,
                    })

            return jsonify(ret_data)
        else:
            # return default resource info
            return jsonify(ret_data)

    def check_file_cache(self, filepattern_list):
        if filepattern_list is None or len(filepattern_list) == 0:
            return list(), 0, 0

        ret_filelist = list()
        total_filesize = 0
        total_cachesize = 0
        filelist = list()
        for each_pattern in filepattern_list:
            pattern = os.path.join(self.dfs_root, each_pattern)
            filelist += glob2.glob(pattern)

        for abspath in filelist:
            LOG.debug("checking cache file of %s" % abspath)
            if os.path.isfile(abspath) is not True:
                continue
            filesize = os.path.getsize(abspath)
            total_filesize += filesize
            import pdb;pdb.set_trace()
            if self.file_cache_monitor.check_file(abspath, is_abspath=True) is True:
                relpath = os.path.relpath(abspath, self.dfs_root)
                ret_filelist.append(relpath)
                total_cachesize += filesize
            ret_filelist.sort()
        return ret_filelist, total_filesize, total_cachesize


class CacheInfo(Resource):
    file_cache_monitor = None

    def __init__(self, *args, **kwargs):
        super(CacheInfo, self).__init__(*args, **kwargs)
        try:
            if self.file_cache_monitor is None:
                self.file_cache_monitor = file_cache.get_instance()
        except file_cache.CacheMonitorError as e:
            self.file_cache_monitor = None

    def get(self):
        ret_data = {}
        if self.file_cache_monitor is not None:
            filecache_ret = self.file_cache_monitor.cached_files()
            ret_data = {ResourceConst.APP_CACHE_FILES: filecache_ret}
        return jsonify(ret_data)


if __name__ == "__main__":
    try:
        # run REST server
        app = Flask(__name__)
        api = restful.Api(app)
        api.add_resource(ResourceInfo, '/api/v1/resource/')
        # do no turn on debug mode. it make a mess for graceful terminate
        host = "0.0.0.0"; port = 8022
        app.run(host=host, port=port, threaded=True, debug=True)
    except KeyboardInterrupt as e:
        ret_code = 1
    finally:
        pass
