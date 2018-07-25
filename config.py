# all configuration variables for the entire program

# starting point for the search
start = {
    "O2" : 0.05,
    "H2" : 0.20,
    "other" : 0.50,
    "filler" : 0.25
    }

# increment dictionary to defien the step sizes for the search
increment_dict = {
    "O2" : {1 : 0.1},
    "H2" : {1 : 0.1}
    }


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
