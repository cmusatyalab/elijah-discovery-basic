RESTful registration server
----------------------------

Central directory server using RESTful API



Tested platform
--------------------
Ubuntu 12.04 LTS 64 bit
Red Hat Enterprise Linux Server release 6.5 (Santiago)



Installation
-------------

To install, you need

	# For Ubuntu

	> $ sudo apt-get install mysql-server python-mysqldb python-dev libmysqlclient-dev 
	> $ sudo pip install -r requirements.txt

	# For RHEL

	Make sure to install libxml2-devel.x86_64, libxslt-devel.x86_64, and python-dev for lxml installation


Then, create user/database at mysql and register it at mysql.conf file at
project directory. For example,

    > $ mysql -u root -p 
	> mysql> CREATE USER 'cloudlet'@'localhost' IDENTIFIED BY 'cloudlet';
	> mysql> GRANT ALL PRIVILEGES ON *.* TO 'cloudlet'@'localhost';
	> mysql> FLUSH PRIVILEGES;
	> mysql> CREATE DATABASE cloudlet_registration;
		
	> $ cat mysql.conf 
	> [client]
	> database = cloudlet_registration
	> user = cloudlet
	> password = cloudlet
	> default-character-set = utf8
	> $


Finally, you need IP geolocation DB to estimate location of Cloudlet machine.
In this example, we use GeoLite. GeoLite databases are distributed under the
[Creative Commons Attribution-ShareAlike 3.0 Unported
License](http://creativecommons.org/licenses/by-sa/3.0/)

    > This project includes GeoLite data created by MaxMind, available from
    > <a href="http://www.maxmind.com">http://www.maxmind.com</a>. 


You can download GeoLite from [link](http://dev.maxmind.com/geoip/geolite).  Or
execute download_geoip_db.sh as follows:

		$ ./download_geoip_db.sh


