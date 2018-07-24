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


# scripts
import rediswq
from starter import start



host="redis"
# Uncomment next two lines if you do not have Kube-DNS working.
# import os
# host = os.getenv("REDIS_SERVICE_HOST")
q = rediswq.RedisWQ(name="job2", host="redis")


while not q.kill():
    item = q.lease(lease_secs=10, block=True, timeout=2) #CHANGE? the lease n timeout?
    if item is not None:
        param_code = item.decode("utf=8")
        q.put(value=param_code, queue="run")
        #sql.run_db(data=input_parameters)
        '''
        PYATMOS GOES HERE
        '''
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
            else:
                q.put(value=param_code, queue="complete0")

    else:
        print("Waiting for work")
print("Queue empty, exiting")