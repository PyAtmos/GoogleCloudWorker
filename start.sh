#! /bin/bash
cd /home/kuber-master/
sudo git fetch origin
sudo git reset --hard origin/master
cd /home/pyatmos/
sudo git fetch origin
sudo git reset --hard origin/master
cd /home/
sudo python3 /home/kuber-master/worker.py
ting=$(curl http://metadata.google.internal/computeMetadata/v1/instance/name -H "Metadata-Flavor: Google")
gcloud compute instances delete $ting --zone=us-west1-b --delete-disks=all