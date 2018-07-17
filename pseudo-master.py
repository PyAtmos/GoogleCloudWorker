# pseudo code for the master

import numpy as np
import hashlib
from copy import deepcopy

# create the SQL database

# create container with 2*p nodes where p is the number of parameters we are searching through for the atmos model
# start master with initial point:

# function: given a platform point, find neighbors, check comformatiy with rules, add to job queue, and add to sql db

def build_queue(platform, increment_dict, job_queue, step_size=1, search_mode="sides"):
	# let's say platform is not a list of values but a dictionary:
	#platform = {
	#			"O2" : .05,
	#			"H2" : 0.21,
	#			"other" : constant_value,
	#			"filler" : dynamic value to help reach 100% sum
	#			}
	#increment_dict = {
	#			"H2" : {.001: 0.0001, 0.01: 0.001, ...}
	#			}
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
				inDB = check_DB(neighbor)
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
				job_queue.add(neighbor)
				add_DB(neighbor)
				added_2_queue = True	


	# ...so did we actually add any neighbors to the queue
	if not added_2_queue:
		# do we want to do anything here?
		#check job_queue size...if it's 0
		#check worker_queue size...if it's the same size as number of workers total
		#then no one is working and there is nothing to work on
		if (job_queue.size()==0) & (worker_queue.size()==n_workers):
			# we reached the border


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

def hash_param(platform):
	string = ""
	for molecule, concentration in platform.items():
		string += molecule
		string += str(concentration)
	hash_object = hashlib.md5(str.encode(string))
	return hash_object.hexdigest()
