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

import libvirt
import ResourceConst as Const
import time


class ResourceMonitorError(Exception):
    pass


class ResourceMonitor(object):
    def __init__(self, openstack_stats=None, log=None):
        if log:
            self.log = log
        else:
            self.log = open("/dev/null", "w+b")
        self.openstack_stats = None
        self.cpu_monitor = None
        self.libvirt_conn = None
        
        if openstack_stats:
            # OpenStack
            self.openstack_stats = openstack_stats
        else:
            # Stand-alone
            self.conn = libvirt.open("qemu:///session")
            self.cpu_monitor = CPUMonitor()

    def get_static_resource(self):
        mem_total = 0
        number_total_cores = 0
        clock_speed = 0

        if self.openstack_stats:
            number_total_cores = self.openstack_stats.get("vcpus")
            mem_total = self.openstack_stats.get("memory_mb")
            clock_speed = -1
        else:
            if not self.conn:
                return dict()
            machine_info = self.conn.getInfo()
            mem_total = machine_info[1]
            clock_speed = machine_info[3]
            number_socket = machine_info[5]
            number_cores = machine_info[6]
            number_threads_pcore = machine_info[7]
            number_total_cores = int(number_socket*number_cores*number_threads_pcore)

        info_dict = {
                Const.TOTAL_CPU_NUMBER: int(number_total_cores),
                Const.CLOCK_SPEED: float(clock_speed),
                Const.TOTAL_MEM_MB: long(mem_total),
                }
        return info_dict

    def get_dynamic_resource(self):
        if self.openstack_stats:
            total_cores = self.openstack_stats.get("vcpus")
            used_cores = self.openstack_stats.get("vcpus_used")
            cpu_usage = used_cores*100.0/total_cores
            free_memory = self.openstack_stats.get("free_ram_mb")
        else:
            cpu_usage = float(self.cpu_monitor.get_usage())
            if self.conn:
                memory_info = self.conn.getMemoryStats(-1, 0)
                free_memory = memory_info['cached'] + memory_info['free']
                free_memory = long(free_memory/1024)
        
        info_dict = {
                Const.TOTAL_CPU_PERCENT: cpu_usage,
                Const.TOTAL_MEM_FREE_MB: free_memory,
                }
        return info_dict

    def terminate(self):
        pass


class CPUMonitor:
    def __init__(self, interval=0.1, percentage=True):
        self.interval = interval

    def get_time(self):
        stat = file("/proc/stat", "r")
        time_list = stat.readline().split(" ")[2:6]
        stat.close()
        for index in range(len(time_list)):
            time_list[index] = int(time_list[index])
        return time_list 
    
    def get_usage(self):
        before = self.get_time()
        time.sleep(self.interval)
        after = self.get_time()
        delta = list()
        for index in range(len(before)):
            delta.append(after[index] - before[index])
        result= 100 - (delta[len(delta)-1]*100.00/sum(delta))
        return result


if __name__ == "__main__":
    from pprint import pprint
    monitor = get_instance()
    pprint(monitor.get_static_resource())
    pprint(monitor.get_dynamic_resource())
    


