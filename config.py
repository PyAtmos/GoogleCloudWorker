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

# increment dictionary to defien the step sizes for the search
increment_dict = {
    "O2" : {1.0 : 0.001},
    "N2" : {1.0 : 0.0},
    "H2O" : {1.0 : 0.0001},
    "CH4" : {1.0 : 0.00000001},
    "CO2" : {1.0 : 0.00001},
    "H2" : {1.0 : 0.0000000001},
    }

ALTER_MOLECULES = ["O2"]



MAX_JOB_RUN_TIME = 5*60*60 #in seconds

# GCE Info
PROJECT_ID = 'i-agility-205814'

# SQL Server Info
CLOUDSQL_SERVER_USER = 'root'
CLOUDSQL_SERVER_PASSWORD = 'AreWeAlone'
CLOUDSQL_SERVER_ID = 'sql-server'
CLOUDSQL_SERVER_IP = '35.233.245.129'
CLOUDSQL_SERVER_REGION = "us-west1"
CLOUDSQL_DATABASE = 'test' #'pyatmos'

# Redis Server Info
REDIS_SERVER_IP = '10.138.0.21'
REDIS_SERVER_NAME = 'pyatmos' #not an official name, just a consistent reference-name throughout this program
