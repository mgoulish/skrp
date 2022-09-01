#! /bin/bash

PID=$1

while [ 1 ]
do
  top -H -w 500 -bn 1 -p ${PID} | grep core_thread 
  sleep 5
done

