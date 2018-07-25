# SOURCE: for only the redis part
#https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/

# packages
import numpy as np
import hashlib
from copy import deepcopy
import os
import sys
import time
from datetime import datetime

# pyatmos  
import pyatmos 


# scripts
import rediswq
import utilities
from starter import start



q = rediswq.RedisWQ(name="job2", host=utilities.redis_host)
while not q.kill():
    item = q.lease(lease_secs=10, block=True, timeout=2) #CHANGE? the lease n timeout?
    if item is not None:
        param_code = item.decode("utf=8")
        q.put(value=param_code, queue="run")
        #sql.run_db(data=input_parameters)
        param_dict = utilities.param_decode(param_code)

        '''
        PYATMOS GOES HERE
        '''
        # TESTING
        atmos = pyatmos.Simulation()
        atmos.start()
        run_code = atmos.run(species_concentrations={}, max_photochem_iterations=10000, n_clima_steps=400, output_directory='/home/willfaw/results')


        #q.complete(item)
        if errored:
            q.put(value=param_code, queue="error")
            #sql.error_db(msg, data=input_parameters)
        else:
            #q.put(value=itemstr, queue="complete")
            #sql.complete_db(msg, data=input_parameters)
            if stable:
                # find neighbors and add to queue
                #explore(input_parameters, increment_dict, q, step_size=2)
                q.put(value=param_code, queue="complete1")
                param_dict = utilities.param_decode(param_code)
                utilities.explore(
                    param_dict=param_dict,
                    increment_dict=increment_dict,
                    redis_db=q,
                    step_Size=2,
                    search_mode="sides")
            else:
                q.put(value=param_code, queue="complete0")

    else:
        print("Waiting for work")
print("Queue empty, exiting")
