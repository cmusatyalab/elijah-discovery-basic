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


class AppInfo(object):
    APPLICATION     = "application"
    APP_ID          = "app-id"
    REQUIRED_RTT             = "required-RTT"
    REQUIRED_CACHE_FILES     = "required-files"
    REQUIRED_CACHE_URLS      = "required-URLs"
    REQUIRED_MIN_CPU_CLOCK   = "required-cpu-clocks"

    WEIGHT_RTT      = "weight-RTT"
    WEIGHT_CACHE    = "weight-cache"
    WEIGHT_RESOURCE = "weight-resource"

    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)
    
    def __getitem__(self, name):
        return self.__dict__.get(name, None)

    def get_info(self):
        return {self.APPLICATION: self.__dict__}


