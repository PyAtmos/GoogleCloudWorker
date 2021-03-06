#!/usr/bin/env python

# utility file for keeping consistent language in handling parameters

####################################################################################################
# SCRIPTS
from config import *

# PACKAGES
import hashlib
import numpy as np
from copy import deepcopy


####################
### Parameter Conversions
def param_encode(param_dict):
    param_str = ""
    for molecule in ATMOS_MOL:
        #string += molecule
        concentration = param_dict[molecule]
        param_str += str(concentration)
        param_str += ","
    param_str = param_str[:-1] #remove trailing comma
    return param_str

def param_decode(param_str):
    param_list = param_str.split(",")
    param_dict = {}
    for i, molecule in enumerate(ATMOS_MOL):
        param_dict[molecule] = param_list[i]
    return param_dict

def param_hash(param_dict):
    string = ""
    for molecule in ATMOS_MOL:
        string += molecule
        concentration = param_dict[molecule]
        string += str(concentration)
    hash_object = hashlib.md5(str.encode(string))
    return hash_object.hexdigest()

def metadata_encode(meta_dict):
    meta_str = ""
    for key in ATMOS_METADATA:
        meta_str += str(meta_dict[key])
        meta_str += ','
    meta_str = meta_str[:-1] #remove trailing comma
    return meta_str

def metadata_decode(meta_str):
    meta_list = meta_str.split(",")
    meta_dict = {}
    for i, key in enumerate(ATMOS_METADATA):
        meta_dict[key] = meta_list[i]
    return meta_dict

def pack_items(item_list):
    # take a list of items and pack them into a string separated by a semicolon
    packed = ';'.join(map(str, item_list))
    return packed

def unpack_items(packed_items):
    unpacked = packed_items.split(";")
    return unpacked




####################
### Build Functions
def round_partial(value, resolution):
    return round(float(value)/float(resolution)) * resolution

def calc_filler(param_dict):
    filler = 1 # starting point
    for molecule, concentration in param_dict.items():
        concentration = float(concentration)
        if molecule not in ["N2"]:
            filler -= concentration
        else:
            continue
    return round(filler, 10) #10 digits because that's the smallest digit it should go to


####################
### Explore Functions
def explore(param_dict, increment_dict, redis_db, step_size=1, search_mode="sides", explore_count="0"):
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
        for molecule in ALTER_MOLECULES:
            concentration = float(param_dict[molecule])
            mol_increment_dict = increment_dict[molecule]
            for b, bin in enumerate(mol_increment_dict['bins']):
                if concentration < bin:
                    break
                else:
                    continue
            increment = mol_increment_dict['increment'][b]
            if increment == 0:
                continue #skip this molecule
            else:
                pass
            for direction in steps:
                neighbor = deepcopy(param_dict)
                val = round_partial(concentration + direction*increment, increment)
                if val > 0:
                    neighbor[molecule] = val
                else:
                    continue
                neighbor["N2"] = calc_filler(neighbor)
                if neighbor["N2"] < 0:
                    # impossible space...don't add
                    continue
                else:
                    # add to main queue and sql queue
                    #redis_db.put(value=neighbor, queue="main")
                    packed_list = pack_items( [param_encode(neighbor), param_hash(param_dict), explore_count] )
                    redis_db.put(value=packed_list, queue="main sql")

    elif search_mode == "diagonals":
        # say if we have 's' possible states...s=3 for step_size=1 st we can go +1, +0, or -1.
        # and if we have 'd' number of dimensions to explore...dimensions is number of molecules we're exploring
        # then we'll have (s^d - 1) neighbors to search for
        # idea, create
        next_list = [param_dict]
        for molecule in ALTER_MOLECULES:
            concentration = float(param_dict[molecule])
            mol_increment_dict = increment_dict[molecule]
            previous_list = deepcopy(next_list)
            for direction in steps:
                for neighbor in previous_list:
                    neigh = deepcopy(neighbor)
                    for b, bin in enumerate(mol_increment_dict['bins']):
                        if concentration < bin:
                            break
                        else:
                            continue
                    increment = mol_increment_dict['increment'][b]
                    if increment == 0:
                        continue #skip this molecule
                    else:
                        pass
                    val = round_partial(concentration + direction*increment, increment)
                    if val > 0:
                        neigh[molecule] = val
                        next_list.append(neigh)
                    else:
                        continue
        # now have a list of all possible neighboring points
        for neighbor in next_list:
            neighbor["N2"] = calc_filler(neighbor)
            if neighbor["N2"] < 0:
                # impossible space...don't add
                continue
            else:
                # add to main queue and sql queue
                #redis_db.put(value=neighbor, queue="main")
                packed_list = pack_items( [param_encode(neighbor), param_hash(param_dict), explore_count] )
                redis_db.put(value=packed_list, queue="main sql")
    
    else:
        # no other search_mode created
        pass