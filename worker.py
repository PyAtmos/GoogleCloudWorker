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
local_output_directory = '/home/willfaw/results'

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
            """
            possible returned string as atmos_output:
              'success'
              'photochem_error'
              'clima_error' 
            """
            atmos_output = atmos.run(species_concentrations=param_dict,
                                    max_photochem_iterations=10000,
                                    max_clima_steps=400,
                                    output_directory=local_output_directory)
            
            stable_atmosphere = ""
            #for now, just assume stable if atmos_output is 'success'
            if atmos_output == "success":
                stable_atmosphere = True
            else:
                # later build out rules to differentiate stable n unstable for a completed run
                pass

            """
            atmos run_metadata_dict:
                'start_time' : self._start_time,
                'photochem_duration' : self._photochem_duration,
                'photochem_iterations' : self._n_photochem_iterations,  
                'clima_duration' : self._clima_duration,
            #    'clima_iterations' : self._n_clima_iterations, # TO DO, clima iterations not set   
                'run_duraton' : self._run_time_end - self._run_time_start,
                'input_max_clima_iterations' : self._max_clima_steps,
                'input_max_photochem_iterations' : self._max_photochem_iterations,
            #    'input_species_concentrations' : self._species_concentrations

            see config.py for list of values from run_metadata_dict that we care about
            """
            atmos.write_metadata(local_output_directory+'/run_metadata.json')
            run_metadata_dict = atmos.get_metadata()

            # pack info to be queued to output
            metadata_code = utilities.metadata_encode(run_metadata_dict)
            packed_output_code = utilities.pack_items( [param_code, atmos_output, stable_atmosphere, metadata_code] )
            # TESTING
            ##########PYATMOS##########

            ###########################
            # Store pyatmos results on google cloud 
            ###########################

            # get list of files in output directory
            file_list = os.listdir(local_output_directory)

            # upload files to google cloud bucket 
            blob_output_dir = JOB_STORAGE_PATH + '/' + parah_hash 
            for file_name in file_list: 
                blob = gcs_bucket.blob(blob_output_dir + '/' + file_name) 
                blob.upload_from_filename(file_name) 


            # remove item off processing/lease queue
            q.complete(param_code)
            q.put(value=packed_output_code, queue="complete")
            
            if stable_atmosphere:
                param_dict = utilities.param_decode(param_code)
                utilities.explore(
                    param_dict=param_dict,
                    increment_dict=increment_dict,
                    redis_db=q,
                    step_size=2,
                    search_mode="sides")
            else:
                pass
        else:
            #print("Waiting for work")
            #time.sleep(5)
            pass
    else:
        #print("Waiting for work")
        #time.sleep(5)
        pass
