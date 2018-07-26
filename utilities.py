# utility file for keeping consistent language in handling parameters

####################################################################################################
# SCRIPTS
from config import *

# PACKAGES
import hashlib
import numpy as np


####################
### Parameter Conversions
def param_encode(param_dict):
    param_str = ""
    for molecule, _ in start.items():
        #string += molecule
        concentration = param_dict[molecule]
        param_str += str(concentration)
        param_str += ","
    param_str = param_str[:-1] #remove trailing comma
    return param_str

def param_decode(param_str):
    param_list = param_str.split(",")
    param_dict = {}
    for i, (molecule,_) in enumerate(start.items()):
        param_dict[molecule] = param_list[i]
    return param_dict

def param_hash(param_dict):
    string = ""
    for molecule, _ in start.items():
        string += molecule
        concentration = param_dict[molecule]
        string += str(concentration)
    hash_object = hashlib.md5(str.encode(string))
    return hash_object.hexdigest()


####################
### Build Functions
def round_partial(value, resolution):
    return round(float(value)/float(resolution), resolution)

def calc_filler(param_dict):
    filler = 1 # starting point
    for molecule, concentration in param_dict.items():
        if molecule not in ["filler"]:
            filler -= concentration
        else:
            continue
    return filler


####################
### Explore Functions
def explore(param_dict, increment_dict, redis_db, step_size=1, search_mode="sides"):
    # let's say param_dict is not a list of values but a dictionary:
    #param_dict = {
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
    steps = np.concatenate((-1*(np.arange(step_size)+1),np.arange(step_size)+1))
    if search_mode == "sides":
        for molecule, concentration in param_dict.items():
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
                neighbor = deepcopy(param_dict)
                neighbor[molecule] = round_partial(concentration + direction*increment, increment)
                neighbor["filler"] = calc_filler(neighbor)
                if neighbor["filler"] < 0:
                    # impossible space...don't add
                    continue
                else:
                    # add to main queue and sql queue
                    #redis_db.put(value=neighbor, queue="main")
                    redis_db.put(value=neighbor, queue="main sql")

    elif search_mode == "diagonals":
        # say if we have 's' possible states...s=3 for step_size=1 st we can go +1, +0, or -1.
        # and if we have 'd' number of dimensions to explore...dimensions is number of molecules we're exploring
        # then we'll have (s^d - 1) neighbors to search for
        # idea, create
        previous_list = [param_dict]
        for molecule, concentration in param_dict:
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
            neighbor["filler"] = calc_filler(neighbor)
            if neighbor["filler"] < 0:
                # impossible space...don't add
                continue
            else:
                # add to main queue and sql queue
                #redis_db.put(value=neighbor, queue="main")
                redis_db.put(value=neighbor, queue="main sql")
    
    else:
        # no other search_mode created
        pass