#!/usr/bin/env python 
#
# Elijah: Cloudlet Infrastructure for Mobile Computing
# Copyright (C) 2011-2012 Carnegie Mellon University
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of version 2 of the GNU General Public License as published
# by the Free Software Foundation.  A copy of the GNU General Public License
# should have been distributed along with this program in the file
# LICENSE.GPL.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#

import sys
import socket
import pprint
import random
import urllib
import time
import httplib
import json
import threading
from optparse import OptionParser
from urlparse import urlparse

import ResourceConst
import logging
from app_info import AppInfo
from synthesis_client import Client as SynthesisClient
from synthesis_client import Protocol
from synthesis_client import ClientError


# Logging
LOG = logging.getLogger("discovery")
LOG.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
ch.setFormatter(formatter)
LOG.addHandler(ch)


class CloudletDiscoveryClientError(Exception):
    pass


class CloudletQueryingThread(threading.Thread):
    def __init__(self, cloudlet_info, app_info=None):
        self.cloudlet_info = cloudlet_info
        self.url = "http://%s:%d%s" % (
                cloudlet_info['ip_address'],
                cloudlet_info['rest_api_port'],
                cloudlet_info['rest_api_url'])
        self.app_info = app_info
        threading.Thread.__init__(self, target=self.get_info)

    def get_info(self):
        try:
            LOG.info("Connecting to cloudlet at %s" % self.url)
            end_point = urlparse(self.url)
            if self.app_info is not None:
                params = json.dumps(self.app_info.get_info())
            else:
                params = json.dumps({})
            headers = {"Content-type": "application/json"}
            conn = httplib.HTTPConnection(end_point.hostname, \
                    end_point.port, timeout=10)
            LOG.debug("Query parameter:")
            LOG.debug((pprint.pformat(json.loads(params))))
            conn.request("GET", "%s" % end_point[2], params, headers)
            data = conn.getresponse().read()
            json_data = json.loads(data)
            self.cloudlet_info.update(json_data)
        except socket.error as e:
            LOG.error(str(e) + "\n")


class CloudletDiscoveryClient(object):
    API_URL             =   "/api/v1/Cloudlet/search/"

    def __init__(self, register_server):
        self.register_server = register_server
        if self.register_server.find("http://") != 0:
            self.register_server = "http://" + self.register_server
        if self.register_server.endswith("/") != 0:
            self.register_server =self.register_server[:-1]

    def get_time_measurement(self):
        if hasattr(self, "time_to_cloud"):
            msg = "Time from get cloudlet list from cloud:\t%f\n" % \
                    (self.time_to_cloudlet-self.time_to_cloud)
            msg += "Time from get detail cloudlet info:\t%f\n" % \
                    (self.time_from_cloudlet-self.time_to_cloudlet)
            msg += "Time to make a decision:\t\t%f\n" % \
                    (self.time_end-self.time_from_cloudlet)
            msg += "Total time:\t\t\t\t%f\n" % (self.time_end-self.time_to_cloud)
        else:
            msg = "No measurement result\n"
        return msg

    def find_by_ip(self, client_ip=None, app_info=None):
        self.time_to_cloud = time.time()
        cloudlet_list = self._search_by_proximity(client_ip=client_ip)
        self.time_to_cloudlet = time.time()
        self._get_cloudlet_infos(cloudlet_list, app_info)
        self.time_from_cloudlet = time.time()
        cloudlet = self.find_best_cloudlet(cloudlet_list, app_info)
        self.time_end = time.time()
        return cloudlet

    def find_by_gps(self, latitude, longitude, app_info=None):
        cloudlet_list = self._search_by_proximity(latitude=latitude, 
                longitude=longitude)
        self._get_cloudlet_infos(cloudlet_list, app_info)
        cloudlet = self.find_best_cloudlet(cloudlet_list, app_info)
        return cloudlet

    def _search_by_proximity(self, client_ip=None, \
            latitude=None, longitude=None, n_max=3):

        # get cloudlet list
        if latitude is not None and longitude is not None:
            end_point = urlparse("%s%s?n=%d&latitude=%s&longitude=%s" % \
                    (self.register_server, CloudletDiscoveryClient.API_URL, \
                    n_max, latitude, longitude))
        elif client_ip is not None:
            # search by IP address
            end_point = urlparse("%s%s?n=%d&client_ip=%s" % \
                    (self.register_server, CloudletDiscoveryClient.API_URL, \
                    n_max, str(client_ip)))
        else:
            end_point = urlparse("%s%s?n=%d" % \
                    (self.register_server, CloudletDiscoveryClient.API_URL, \
                    n_max))
        try:
            self.cloudlet_list = http_get(end_point)
        except socket.error as e:
            CloudletDiscoveryClient("Cannot connect to ")
        return self.cloudlet_list

    def _get_cloudlet_infos(self, cloudlet_list, app_info):
        thread_list = list()
        for cloudlet in cloudlet_list:
            new_thread = CloudletQueryingThread(cloudlet, app_info)
            thread_list.append(new_thread)
        for th in thread_list:
            th.start()
        for th in thread_list:
            th.join()

    def find_best_cloudlet(self, cloudlet_list, app_info=None):
        # pre-screening conditions
        item_len = len(cloudlet_list)
        if item_len == 0:
            msg = "No available cloudlet at the list\n"
            raise CloudletDiscoveryClientError(msg)
        if item_len == 1:
            LOG.info("Only one cloudlet is available")
            return cloudlet_list[0]

        # filterout using required conditions
        filtered_cloudlet = list(cloudlet_list)
        for cloudlet in cloudlet_list:
            # check CPU min
            required_clock_speed = getattr(app_info, AppInfo.REQUIRED_MIN_CPU_CLOCK, None)
            cloudlet_cpu_speed = cloudlet.get(ResourceConst.CLOCK_SPEED)
            if required_clock_speed is not None:
                if cloudlet_cpu_speed < required_clock_speed:
                    filtered_cloudlet.remove(cloudlet)
            # check rtt
            #required_rtt = getattr(app_info, AppInfo.REQUIRED_RTT, None)
            #cloudlet_rtt = getattr(cloudlet, ResourceConst.RTT_BETWEEN_CLIENT, None)
            #if required_rtt is not None:
            #    if cloudlet_rtt < required_rtt:
            #        filtered_cloudlet.append(cloudlet)
        if len(filtered_cloudlet) == 0:
            LOG.warning("No available cloudlet after filtering out")
            return None

        # check cache
        max_cache_score = float(-1)
        max_cache_cloudlet = None
        for cloudlet in filtered_cloudlet:
            cache_score = cloudlet.get(ResourceConst.APP_CACHE_TOTAL_SCORE, None)
            if cache_score is not None and cache_score > max_cache_score:
                max_cache_score = cache_score
                max_cache_cloudlet = cloudlet
        if max_cache_cloudlet is not None:
            return max_cache_cloudlet
        else:
            return filtered_cloudlet[0]


        # check application preference
        #weight_rtt = getattr(app_info, AppInfo.KEY_WEIGHT_CACHE, None)
        #weight_cache = getattr(app_info, AppInfo.KEY_WEIGHT_CACHE, None)
        #weight_resource = getattr(app_info, AppInfo.KEY_WEIGHT_CACHE, None)
        #if weight_rtt is None or weight_cache is None or \
        #        weight_resource is None:
        #    index = random.randint(0, item_len-1)
        #    return cloudlet_list[index]




    def terminate(self):
        pass


def http_get(end_point):
    LOG.info("Connecting to %s" % (end_point.geturl()))
    params = urllib.urlencode({})
    headers = {"Content-type":"application/json"}
    end_string = "%s?%s" % (end_point[2], end_point[4])

    conn = httplib.HTTPConnection(end_point[1])
    conn.request("GET", end_string, params, headers)
    data = conn.getresponse().read()
    response_list = json.loads(data).get('cloudlet', list())
    conn.close()
    return response_list


def process_command_line(argv):
    USAGE = 'Usage: %prog [-d dns_server|-s register_server]'
    DESCRIPTION = 'Cloudlet register thread'

    parser = OptionParser(usage=USAGE, description=DESCRIPTION)

    parser.add_option(
            '-d', '--dns_server', action='store', dest='dns_server',
            default=None, help='IP address of DNS server')
    parser.add_option(
            '-s', '--register_server', action='store', dest='register_server',
            default=None, help='IP address of cloudlet register server')
    parser.add_option(
            '-a', '--latitude', action='store', type='string', dest='latitude',
            default=None, help="Manually set cloudlet's latitude")
    parser.add_option(
            '-o', '--longitude', action='store', type='string', dest='longitude',
            default=None, help="Manually set cloudlet's longitude")
    parser.add_option(
            '-c', '--client-ip', action='store', type='string', dest='client_ip',
            default=None, help="Manually set cloudlet's longitude")
    parser.add_option(
            '-f', '--overlay-file', action='store', type='string', dest='overlay_file',
            default=None, help="Specify the VM overlay file path")
    parser.add_option(
            '-u', '--overlay-URL', action='store', type='string', dest='overlay_url',
            default=None, help="Specify the VM overlay URL")
    settings, args = parser.parse_args(argv)

    if settings.dns_server == None and settings.register_server == None:
        parser.error("need either dns or register server")
    if settings.dns_server is not None and settings.register_server is not None:
        parser.error("need either dns or register server")

    if settings.overlay_file is not None and settings.overlay_url is not None:
        parser.error("You cannot specify both overlay file and overlay URL")

    return settings, args


def get_ip(iface = 'eth0'):
    import socket
    import struct
    import fcntl
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockfd = sock.fileno()
    SIOCGIFADDR = 0x8915

    ifreq = struct.pack('16sH14s', iface, socket.AF_INET, '\x00' * 14)
    try:
        res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except:
        return None
    ip = struct.unpack('16sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)


def main(argv):
    settings, args = process_command_line(sys.argv[1:])
    cloudlet = None
    app_info = AppInfo(**{
        AppInfo.APP_ID: "moped",
        AppInfo.REQUIRED_RTT: 30,
        AppInfo.REQUIRED_MIN_CPU_CLOCK: 1600, # in MHz
        AppInfo.REQUIRED_CACHE_URLS:[
            "http://amazon-asia.krha.kr/overlay-webapp-face.zip",
            "http://krha.kr/data/publications/mobisys203-kiryong.pdf",
            ],
        AppInfo.REQUIRED_CACHE_FILES:[
            "moped/**/*.xml",
            ]
        })

    # find the best cloudlet querying to the registration server
    if settings.register_server is not None:
        client = CloudletDiscoveryClient(settings.register_server)
        if settings.latitude is not None and settings.longitude is not None:
            cloudlet = client.find_by_gps(settings.latitude, \
                    settings.longitude, app_info=app_info)
        elif settings.client_ip is not None:
            cloudlet = client.find_by_ip(settings.client_ip, \
                    app_info=app_info)
        else:
            cloudlet = client.find_by_ip(app_info=app_info)
        LOG.debug("Query results:")
        LOG.debug(pprint.pformat(cloudlet))
        LOG.debug("Time Measurement")
        LOG.debug("%s" % client.get_time_measurement())

    # perform cloudlet provisioning using given VM overlay
    if cloudlet and (settings.overlay_file or settings.overlay_url):
        synthesis_client = None
        # provision the back-end server at the Cloudlet
        ip_addr = cloudlet.get("ip_address")
        port = SynthesisClient.CLOUDLET_PORT
        synthesis_option = dict()
        synthesis_option[Protocol.SYNTHESIS_OPTION_DISPLAY_VNC] = False
        synthesis_option[Protocol.SYNTHESIS_OPTION_EARLY_START] = False

        if settings.overlay_file:
            synthesis_client = SynthesisClient(ip_addr, port, overlay_file=settings.overlay_file,
                    app_function=None, synthesis_option=synthesis_option)
        elif settings.overlay_url:
            synthesis_client = SynthesisClient(ip_addr, port, overlay_url=settings.overlay_url,
                    app_function=None, synthesis_option=synthesis_option)

        try:
            synthesis_client.provisioning()
            #synthesis_client.terminate()
            sys.stdout.write("SUCCESS in Provisioning\n")
        except ClientError as e:
            sys.stderr.write(str(e))
        return 1
    return 0


if __name__ == "__main__":
    status = main(sys.argv)
    sys.exit(status)
