#!/bin/bash

wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
gunzip GeoLiteCity.dat.gz
mkdir -p ./cloudlet/network/db/
mv GeoLiteCity.dat ./cloudlet/network/db/
