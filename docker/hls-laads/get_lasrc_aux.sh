#!/bin/bash -x
cd /var/lasrc_aux/
ls 
df -h
cat /etc/fstab
cat /etc/ecs/ecs.config
if [ -n "$LAADS_BUCKET_BOOTSTRAP" ]; then
echo "syncing existing laads data from aws s3 bucket s3://$LAADS_BUCKET_BOOTSTRAP/lasrc_aux/"
aws s3 sync s3://$LAADS_BUCKET_BOOTSTRAP/lasrc_aux/ .
fi

if [ ! -d LADS/2013 ]; then
echo "Archived data not here... fetching 2013-2017 data from USGS."
wget --no-http-keep-alive http://edclpdsftp.cr.usgs.gov/downloads/auxiliaries/lasrc_auxiliary/lasrc_aux.2013-2017.tar.gz
tar -xvzf lasrc_aux.2013-2017.tar.gz
rm lasrc_aux.2013-2017.tar.gz
fi

if [ ! -d MSILUT ]; then
echo "MSILUT data not present... fetching from USGS."
wget --no-http-keep-alive http://edclpdsftp.cr.usgs.gov/downloads/auxiliaries/lasrc_auxiliary/MSILUT.tar.gz
tar -xvzf MSILUT.tar.gz
rm MSILUT.tar.gz
fi

LADSFLAG='--today'
if [ -n "$LAADS_REPROCESS" ]; then
LADSFLAG='--quarterly'
fi
echo "running updatelads.py $LADSFLAG"
updatelads.py $LADSFLAG
echo "Creating listing of dates available."
find . | grep -oP "L8ANC([0-9][0-9][0-9][0-9][0-9][0-9])\.hdf_fused$" > laadsavailable.txt

if [ -n "$LAADS_BUCKET" ]; then
echo "syncing data to s3 bucket s3://$LAADS_BUCKET/lasrc_aux/"
aws s3 sync . s3://$LAADS_BUCKET/lasrc_aux/
fi
