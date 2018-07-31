#!/usr/bin/env python

# SOURCE: for only the redis part
#https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/


####################################################################################################
# PACKAGES
import numpy as np
import hashlib
from copy import deepcopy
import os
import sys
import time
from datetime import datetime

import pyatmos 

# SCRIPTS
import rediswq
import utilities
from config import *

# Cloud storage
from google.cloud import storage



####################
### Start PyAtmos
atmos = pyatmos.Simulation(docker_image="gcr.io/i-agility-205814/pyatmos_docker")
# above docker image uses the 'old' version of atmos
atmos.start()

####################
# conect to GCS storage
gcs_storage_client = storage.Client()
gcs_bucket = gcs_storage_client.get_bucket(CLOUD_BUCKET_NAME) 

####################
### Start the Worker
q = rediswq.RedisWQ(name=REDIS_SERVER_NAME, host=REDIS_SERVER_IP)
while not q.kill():
    if q.size("main") != 0:
        # grab next set of param off queue
        param_code = q.buy(block=True, timeout=30)
        if param_code is not None:
            q.put(value=param_code, queue="run")
            param_dict = utilities.param_decode(param_code)
            param_hash = utilities.param_hash(param_dict)

            ###########################
            # Get the previous solutions file pyatmos run! 
            ###########################
            # TODO!!!!!!!!!!!!!!!!!!

            ##########PYATMOS##########
            atmos_output = atmos.run(species_concentrations=param_dict, max_photochem_iterations=10000, max_clima_steps=400, output_directory='/home/willfaw/results')
            atmos.write_metadata(output_directory+'/run_metadata.json') 
            """
            possible returned string:
              'success'
              'photochem_error'
              'clima_error' 
            """
            #for now, just assume stable
            stable = True
            # TESTING
            ##########PYATMOS##########

            ###########################
            # Store pyatmos results on google cloud 
            ###########################

            # get list of files in output directory
            file_list = os.listdir(output_directory)

            # upload files to google cloud bucket 
            blob_output_dir = JOB_STORAGE_PATH + '/' + parah_hash 
            for file_name in file_list: 
                blob = gcs_bucket.blob(blob_output_dir + '/' + file_name) 
                blob.upload_from_filename(file_name) 


            # remove item off processing/lease queue
            q.complete(param_code)
            if atmos_output in ["photochem_error","clima_error"]: #errored:
                q.put(value=param_code, queue="error")
            else:
                if stable:
                    q.put(value=param_code, queue="complete1")
                    param_dict = utilities.param_decode(param_code)
                    utilities.explore(
                        param_dict=param_dict,
                        increment_dict=increment_dict,
                        redis_db=q,
                        step_size=2,
                        search_mode="sides")
                else:
                    q.put(value=param_code, queue="complete0")
        else:
            #print("Waiting for work")
            #time.sleep(5)
            pass
    else:
        #print("Waiting for work")
        #time.sleep(5)
        pass
