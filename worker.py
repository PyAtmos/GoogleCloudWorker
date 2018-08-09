#!/usr/bin/env python

####################################################################################################
# PACKAGES
import numpy as np
import hashlib
from copy import deepcopy
import os
import sys
import time
from datetime import datetime
import tempfile
import git as gitpython 

import pyatmos 

# SCRIPTS
import rediswq
import utilities
from config import *

# Cloud storage
from google.cloud import storage

###################
### Get git revision sha
try:
    repo = gitpython.Repo(search_parent_directories=True)
    git_revision_sha = repo.head.object.hexsha
except:
    git_revision_sha = 'not_in_repo'

####################
### Start PyAtmos
atmos = pyatmos.Simulation(code_path="/code/atmos") ### CHANGE THIS ###
atmos.start()
####################
# conect to GCS storage
gcs_storage_client = storage.Client()
gcs_bucket = gcs_storage_client.get_bucket(CLOUD_BUCKET_NAME)
initial_local_output_directory = '/results'
####################
### Start the Worker
q = rediswq.RedisWQ(name=REDIS_SERVER_NAME, host=REDIS_SERVER_IP)
ITERATION_NUMBER = 0
while not q.kill():
    if q.size("main") != 0:
        # grab next set of param off queue
        packed_code = q.buy(block=True, timeout=30)
        if packed_code is not None:
            param_code, prev_param_code = utilities.unpack_items(packed_code)
            q.put(value=param_code, queue="run")

            param_dict = utilities.param_decode(param_code)
            param_hash = utilities.param_hash(param_dict)

            for key in param_dict.keys():
                param_dict[key] = float(param_dict[key])

            # Get the previous solutions file pyatmos run! 
            if prev_param_code == "first run":
                prev_param_hash = None
                tmp_photochem_file = None
                tmp_clima_file = None 
            else:
                # previous hashes
                prev_param_dict = utilities.param_decode(prev_param_code)
                prev_param_hash = utilities.param_hash(prev_param_dict)
                # previous photochem 
                tmp_photochem_file = tempfile.NamedTemporaryFile().name
                input_photochem_blob = gcs_bucket.blob(JOB_STORAGE_PATH + '/' + prev_param_hash + '/out.dist')
                input_photochem_blob.download_to_filename(tmp_photochem_file)
                # previous clima
                tmp_clima_file = tempfile.NamedTemporaryFile().name
                input_clima_blob = gcs_bucket.blob(JOB_STORAGE_PATH + '/' + prev_param_hash + '/TempOut.dat') # Temp for temperature here 
                input_clima_blob.download_to_filename(tmp_clima_file)

            ### Run PYATMOS
            ITERATION_NUMBER +=1 
            local_output_directory = initial_local_output_directory + '/{0}'.format(ITERATION_NUMBER) 
            atmos_output = atmos.run(species_concentrations     = param_dict,
                                    max_photochem_iterations    = 10000,
                                    max_clima_steps             = 1000,
                                    output_directory            = local_output_directory,
                                    previous_photochem_solution = tmp_photochem_file,
                                    previous_clima_solution     = tmp_clima_file,
                                    run_iteration_call          = ITERATION_NUMBER,
                                    save_logfiles               = True
                                    )
            # atmos_output could be 'success', 'photochem_error', 'clima_error', 'photochem_nonconverged' 
            stable_atmosphere = "" #for now, just assume stable if atmos_output is 'success'
            if atmos_output == "success":
                stable_atmosphere = True
            else:
                # later build out rules to differentiate stable n unstable for a completed run
                pass

            ### Get Atmos Metadata
            run_metadata_dict = atmos.get_metadata()
            # see config.py for list of values from run_metadata_dict that we care about
            # or go to pyatmos code -> Simulation.get_metadata()

            # add surface temp and pressure to metadata dict
            run_metadata_dict['pressure'] = atmos.get_surface_pressure(local_output_directory+'/parsed_clima_final.csv')
            run_metadata_dict['temperature'] = atmos.get_surface_temperature(local_output_directory+'/parsed_clima_final.csv')
            run_metadata_dict['previous_hash'] = prev_param_hash

            # add surface fluxes for gases we are interested in 
            gases_of_interest = ['H2O', 'CO2', 'CH4', 'CO', 'N2', 'H2O', 'NH3', 'O3']
            gas_fluxes = atmos.get_surface_fluxes(local_output_directory+'/parsed_photochem_fluxes.csv')
            
            # merge dictionaries 
            run_metadata = { **run_metadata, **gas_fluxes }

            # Save the metadata dictionary
            #atmos.write_metadata(local_output_directory+'/run_metadata.json', {'previous_hash' : prev_param_hash, 'current_hash' : param_hash, 'git_revision_sha' : git_revision_sha} )
            with open(local_output_directory+'/run_metadata.json', 'w') as fp:
                json.dump(run_metadata, fp, sort_keys=True, indent=4)


            ### Store pyatmos results on google cloud (will grab all output files automatically) 
            file_list = os.listdir(local_output_directory)
            blob_output_dir = JOB_STORAGE_PATH + '/' + param_hash 
            for file_name in file_list: 
                output_blob = gcs_bucket.blob(blob_output_dir + '/' + file_name) 
                output_blob.upload_from_filename(local_output_directory + '/' + file_name) 

            # remove item off processing/lease queue
            metadata_code = utilities.metadata_encode(run_metadata_dict)
            packed_output_code = utilities.pack_items( [param_code, atmos_output, stable_atmosphere, metadata_code] )
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
            pass
    else:
        pass
