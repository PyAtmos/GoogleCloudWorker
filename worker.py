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


####################
### Start the Worker
q = rediswq.RedisWQ(name=REDIS_SERVER_NAME, host=REDIS_SERVER_IP)
while not q.kill():
    if q.size("main") != 0:
        # grab next set of param off queue
        lease_secs = 60*60*12
        item = q.lease(lease_secs=lease_secs, block=False)
        if item is not None:
            #param_code = item.decode("utf=8")
            q.put(value=param_code, queue="run")
            param_dict = utilities.param_decode(param_code)
            param_hash = utilities.param_hash(param_dict)

            ##########PYATMOS##########
            # TESTING
            atmos = pyatmos.Simulation()
            atmos.start()
            run_code = atmos.run(species_concentrations={}, max_photochem_iterations=10000, n_clima_steps=400, output_directory='/home/willfaw/results')
            ##########PYATMOS##########

            # remove item off processing/lease queue
            q.complete(item)
            if errored:
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
            print("Waiting for work")
            time.sleep(5)
    else:
        print("Waiting for work")
        time.sleep(5)
