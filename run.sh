#!/usr/bin/env bash
export WORKERDIR=/code/kuber-master
export PYATMOSDIR=/code/pyatmos
echo "starting worker ..."
echo $PWD
/usr/bin/python3 /code/kuber-master/worker.py &> /code/kuber-master/run_log.txt
echo "completed worker"
sleep 35000d 
