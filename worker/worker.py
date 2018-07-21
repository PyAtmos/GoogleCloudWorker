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
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import exists, filter_by

# scripts
import sql_create as sql
import rediswq
from starter import start


# functions to handle the real work!
def round_partial(value, resolution):
    return round(float(value)/float(resolution), resolution)

def calc_filler(point):
    filler = 1-point['other'] # starting point...where constants is the concentration of molecules we're holding constant
    for i, concentration in point.items():
        if i no in ["other","filler"]:
            filler -= concentration
        else:
            continue
    return filler

def explore(platform, increment_dict, job_queue, step_size=1, search_mode="sides"):
    # let's say platform is not a list of values but a dictionary:
    #platform = {
    #            "O2" : .05,
    #            "H2" : 0.21,
    #            "other" : constant_value,
    #            "filler" : dynamic value to help reach 100% sum
    #            }
    #increment_dict = {
    #            "H2" : {.001: 0.0001, 0.01: 0.001, ...}
    #            }
    #
    #check to see if any of the neighbors are added to queue or if they've all been executed (dead end)
    added_2_queue = False
    steps = np.concatenate((-1*(np.arange(step_size)+1),np.arange(step_size)+1))
    if search_mode == "sides":
        for molecule, concentration in platform.items():
            if molecule in ["other","filler"]:
                continue
            else:
                pass
            # look up how much we can increment the molecule based off it's concentration
            for max_conc, increment in increment_dict[molecule].items():
                if concentration < max_conc:
                    break
                else:
                    pass
            for direction in steps:
                neighbor = deepcopy(platform)
                neighbor[molecule] = round_partial(concentration + direction*increment, increment)
                neighbor["filler"] = calc_filler(neighbor)
                if neighbor["filler"] < 0:
                    # impossible space...don't add
                    continue
                else:
                    pass
                #check if neighbor point already in DB, if yes then don't add, if no then add
                inDB = sql.exists_db(data=neighbor)
                if in inDB:
                    # already in DB...don't add
                    continue
                else:
                    # add to queue and to DB
                    job_queue.add(neighbor)
                    add_DB(neighbor)
                    added_2_queue = True
    elif search_mode == "diagonals":
        # say if we have 's' possible states...s=3 for step_size=1 st we can go +1, +0, or -1.
        # and if we have 'd' number of dimensions to explore...dimensions is number of molecules we're exploring
        # then we'll have (s^d - 1) neighbors to search for
        # idea, create
        previous_list = [platform]
        for molecule, concentration in platform:
            if molecule in ["other","filler"]:
                continue
            else:
                pass
            previous_list = deepcopy(next_list)
            for direction in steps:
                for neighbor in previous_list:
                    neigh = deepcopy(neighbor)
                    for max_conc, increment in increment_dict[molecule].items():
                        if concentration < max_conc:
                            break
                        else:
                            pass
                    neigh[molecule] = round_partial(concentration + direction*increment, increment)
                    next_list.append(neigh)
        # now have a list of all possible neighboring points
        for neighbor in next_list:
            #check if neighbor point already in DB, if yes then don't add, if no then add
            inDB = check_DB(neighbor)
            if in inDB:
                # already in DB...don't add
                continue
            else:
                # add to queue and to DB
                sql.add_db(neighbor)
                q.put(param_str_enc(start))
                added_2_queue = True








host="redis"
# Uncomment next two lines if you do not have Kube-DNS working.
# import os
# host = os.getenv("REDIS_SERVICE_HOST")

q = rediswq.RedisWQ(name="job2", host="redis")
print("Worker with sessionID: " +  q.sessionID())
print("Initial queue state: empty=" + str(q.empty()))
while not q.empty():
    item = q.lease(lease_secs=10, block=True, timeout=2) #CHANGE? the lease n timeout?
    if item is not None:
        itemstr = item.decode("utf=8")
        print("Working on " + itemstr)
        input_parameters = sql.param_str_dec(itemstr)
        #add to sql db as running
        sql.run_db(data=input_parameters)
        '''
        PYATMOS GOES HERE
        '''
        q.complete(item)
        if errored:
            sql.error_db(msg, data=input_parameters)
        else:
            sql.complete_db(msg, data=input_parameters)
            if stable:
                # find neighbors and add to queue
                explore(input_parameters, increment_dict, q, step_size=2)

    else:
        print("Waiting for work")
print("Queue empty, exiting")