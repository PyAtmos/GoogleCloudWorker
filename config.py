#!/usr/bin/env python

# all configuration variables for the entire program

# initial concentrations of gases 
'''
initial_concentrations = {
        'O2' :  {'concentration' : 2.1E-01,  'certain' : 1},
        'N2' :  {'concentration' : 0.78,     'certain' : 1},
        'H20' : {'concentration' : 1.23E-02, 'certain' : 0},
        'CH4' : {'concentration' : 1.63E-06, 'certain' : 0},
        'CO2' : {'concentration' : 4.00E-04, 'certain' : 0},
        'H2' :  {'concentration' : 8.13E-08, 'certain' : 0}
        }'''

# starting point for the search
start = {
    "O2" : 0.21,
    "N2" : 0.7772982887,
    "H2O" : 0.0123,
    "CH4" : 0.00000163,
    "CO2" : 0.0004,
    "H2" : 0.0000000813,
    }

ATMOS_MOL = ["O2","N2","H2O","CH4","CO2","H2"]#list(start.keys())

# increment dictionary to defien the step sizes for the search
increment_dict = {
    "O2" : {'bins' : [0.3 , 1.0],
            'increment' : [0.02 , 0.05]},
    "N2" : {'bins' : [1.0],
            'increment' : [0.0]},
    "H2O" : {'bins' : [0.9 , 1.0],
            'increment' : [0.1 , 0.0]},
    "CH4" : {'bins' : [0.1 , 1.0],
            'increment' : [0.005 , 0.0]},
    "CO2" : {'bins' : [0.1 , 1.0],
            'increment' : [0.01 , 0.05]},
    "H2" : {'bins' : [0.000000001 , 1.0],
            'increment' : [0.0000000001 , 0.0]},
}
#future:
# "O2" : {'bins' : [0.1, 0.5, 1.0],
#        'increment' : [0.001, 0.01, 0.1]}

ALTER_MOLECULES = ["O2","H2O","CH4","CO2","H2"]


# 'keys' from run_metadata_dict (atmos metadata) that we want to keep and add to sql database
# see notes in worker.py or pyatmos.Simulation.get_metadata()
ATMOS_METADATA = ['atmos_start_time',
                'photochem_duration',
                'photochem_iterations',
                'clima_duration',
                'atmos_run_duration',
                'input_max_clima_iterations',
                'input_max_photochem_iterations',
                'temperature',
                'pressure']


MAX_JOB_RUN_TIME = 5*60*60 #in seconds

# GCE Info
PROJECT_ID = 'i-agility-205814'

# SQL Server Info
CLOUDSQL_SERVER_USER = 'root'
CLOUDSQL_SERVER_PASSWORD = 'AreWeAlone'
CLOUDSQL_SERVER_ID = 'sql-server'
CLOUDSQL_SERVER_IP = '35.233.245.129'
CLOUDSQL_SERVER_REGION = "us-west1"
CLOUDSQL_DATABASE = 'all' #'pyatmos'

# Redis Server Info
REDIS_SERVER_IP = '10.138.0.21'
REDIS_SERVER_NAME = 'pyatmos' #not an official name, just a consistent reference-name throughout this program

# gcloud storage bucket
CLOUD_BUCKET_NAME = 'astrobio'
CLOUD_STORAGE_PATH = 'gs://'+CLOUD_BUCKET_NAME  
JOB_STORAGE_PATH = 'fullrun_results'

