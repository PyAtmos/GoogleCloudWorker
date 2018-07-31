#! /bin/bash
cd /home/kuber-master/
sudo git fetch origin
sudo git reset --hard origin/master
cd /home/
sudo python3 /home/kuber-master/worker.py
