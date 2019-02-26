#!/bin/bash

for k in `ls | grep RUN`
do 
~/oxdna-code/oxDNA/build/bin/oxDNA input conf_file=$k
mv last_conf.dat $k
done