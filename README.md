Elijah: Cloudlet Infrastructure for Mobile Computing
========================================================
A cloudlet is a new architectural element that arises from the convergence of
mobile computing and cloud computing. It represents the middle tier of a
3-tier hierarchy:  mobile device - cloudlet - cloud.   A cloudlet can be
viewed as a "data center in a box" whose  goal is to "bring the cloud closer".

Copyright (C) 2011-2012 Carnegie Mellon University
This is a developing project and some features might not be stable yet.
Please visit our website at [Elijah page](http://elijah.cs.cmu.edu/).



License
----------

All source code and documentation except GeoIP database listed below are
licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0.html).

- To estimate location of the cloudlet, we use GeoIP database named GeoLite
database. GeoLite databases are distributed under the [Creative Commons
Attribution-ShareAlike 3.0 Unported
License](http://creativecommons.org/licenses/by-sa/3.0/)

	> This project includes GeoLite data created by MaxMind, available from <a
	> href="http://www.maxmind.com">http://www.maxmind.com</a>. 



Tested platform
--------------------
Ubuntu 12.04 LTS 64 bit



Installation
-------------

This project is composed of two parts: Cloudlet and Cloud. The role of the
Cloud part is periodically receiving heartbeats from cloudlets and return IP
address of nearby cloudlets using the IP address of the querying client. 

- For Cloudlet

  You will need:
  
  * libvirt python binding 
  * avahi-daemon avahi-python
  * python packages listed at requirements.txt
  
  To install, you need
  
  		> $ sudo apt-get install python-pip python-libvirt avahi-daemon python-avahi
  		> $ sudo pip install -r requirements.txt

  For some distribution, Avahi-daemon doesn't start at boot. You can enable it

  		> $ sudo service avahi-daemon start
  		> $ sudo update-rc.d avahi-daemon defaults
 

- For Cloud

  See [./server/register-rest/README.md](./server/register-rest/README.md)
