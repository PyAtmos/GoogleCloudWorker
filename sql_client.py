# Source:
#https://github.com/GoogleCloudPlatform/getting-started-python/blob/master/2-structured-data/bookshelf/model_cloudsql.py
# And:
#https://cloud.google.com/python/getting-started/using-cloud-sql
# SOURCE: for only the redis part
#https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/

####################################################################################################
# SCRIPTS:
from config import *
import utilities
import rediswq
import argparse

# PACKAGES
import time
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import exists#, filter_by

####################
### Input arguments
parser = argparse.ArgumentParser(description='Grab Master flag')
parser.add_argument('-m', '--master', type=int, default=False,
                    help='if nonzero, assigns node to do the "masters" work')
parser.add_argument('-r', '--reset', type=int, default=False,
                    help='if nonzero, delete existing tables and create new')
parser.add_argument('-c', '--create', type=int, default=False,
                    help='if nonzero, assume no tables exist and create new')
args = parser.parse_args()


####################
### Create SQL Table

Base = declarative_base()
dbFilePath = 'mysql+pymysql://%s:%s@%s:3306/%s' % (CLOUDSQL_SERVER_USER,
                                                CLOUDSQL_SERVER_PASSWORD,
                                                CLOUDSQL_SERVER_IP,
                                                CLOUDSQL_DATABASE)
engine = create_engine(dbFilePath, echo=False)
DBSession = sessionmaker(bind=engine)
session = DBSession()

class ParameterSpace(Base):
    """
    "O2" : 0.21,
    "N2" : 0.7772982887,
    "H2O" : 0.0123,
    "CH4" : 0.00000163,
    "CO2" : 0.0004,
    "H2" : 0.0000000813,
    """
    __tablename__ = 'parameterspace'
    id = Column(Integer, primary_key=True)
    hash = Column(String(256))
    code = String(256)
    O2 = Column(Float)
    N2 = Column(Float)
    H2O = Column(Float)
    CH4 = Column(Float)
    CO2 = Column(Float)
    H2 = Column(Float)
    state = Column(String(256))
    session_start_time = Column(DateTime)
    session_end_time = Column(DateTime)
    bucket_path = Column(String(256))
    # atmos metadata
    stable = Column(String(256))
    atmos_start_time = Column(String(256))
    photochem_duration = Column(String(256))
    photochem_iterations = Column(String(256))
    clima_duration = Column(String(256))
    atmos_run_duraton = Column(String(256))
    input_max_clima_iterations = Column(String(256))
    input_max_photochem_iterations = Column(String(256))
    temperature = Column(String(256))
    pressure = Column(String(256))
    #
    def __init__(self, parameter_dict):
        self.hash = utilities.param_hash(parameter_dict)
        self.code = utilities.param_encode(parameter_dict)
        self.O2 = parameter_dict['O2']
        self.N2 = parameter_dict['N2']
        self.H2O = parameter_dict['H2O']
        self.CH4 = parameter_dict['CH4']
        self.CO2 = parameter_dict['CO2']
        self.H2 = parameter_dict['H2']
        self.state = "queue"
        self.session_start_time = datetime.utcnow()

if args.reset:
    print("Deleting old table...")
    # delete any old table there
    ParameterSpace.__table__.drop(engine)
else:
    pass
if args.create or args.reset:
    print("Creating table...")
    # Create all tables in the engine. This is equivalent to "Create Table" statements in raw SQL.
    Base.metadata.create_all(engine)
else:
    print("Grabbing existing table...")
    pass



####################
### SQL Read + Write Functions

def add_db(data, dtype="dict"):
    # Insert a Person in the person table
    if dtype == "dict":
        dicted = data
    elif dtype == "code":
        dicted = utilities.param_decode(data)
    else:
        return "didn't recognize 'dtype'"
    point = ParameterSpace(dicted)
    session.add(point)
    session.commit()
    return "added: %s" % point.hash

def run_db(data, dtype="dict"):
    if dtype == "dict":
        hashed = utilities.param_hash(data)
    elif dtype == "code":
        dicted = utilities.param_decode(data)
        hashed = utilities.param_hash(dicted)
    else:
        return "didn't recognize 'dtype'"
    point = session.query(ParameterSpace).filter_by(hash=hashed).first()
    point.state = "running"
    session.commit()
    return "running: %s" % point.hash

# def error_db(msg, data, dtype="dict"):
#     if dtype == "dict":
#         hashed = utilities.param_hash(data)
#     elif dtype == "code":
#         dicted = utilities.param_decode(data)
#         hashed = utilities.param_hash(dicted)
#     else:
#         return "didn't recognize 'dtype'"
#     point = session.query(ParameterSpace).filter_by(hash=hashed).first()
#     point.state = "Error"
#     point.error_msg = str(msg) #<-exapnd on this
#     point.end_time = datetime.utcnow()
#     session.commit()
#     return "errored: %s - %s" % (point.hash, msg)


def complete_db(data, run_status, stability, metadata_dict, dtype="dict"):
    if dtype == "dict":
        hashed = utilities.param_hash(data)
    elif dtype == "code":
        dicted = utilities.param_decode(data)
        hashed = utilities.param_hash(dicted)
    else:
        return "didn't recognize 'dtype'"
    point = session.query(ParameterSpace).filter_by(hash=hashed).first()
    point.state = run_status
    point.stable = stability
    point.session_end_time = datetime.utcnow()
    point.bucket_path = JOB_STORAGE_PATH
    # metadata
    # session.commit doesn't acknowledge changes like this: point.__dict__[key] = metadata_dict[key]
    # so hard code the updates for each attribute
    point.atmos_start_time = metadata_dict['atmos_start_time']
    point.photochem_duration = metadata_dict['photochem_duration']
    point.photochem_iterations = metadata_dict['photochem_iterations']
    point.clima_duration = metadata_dict['clima_duration']
    point.atmos_run_duraton = metadata_dict['atmos_run_duraton']
    point.input_max_clima_iterations = metadata_dict['input_max_clima_iterations']
    point.input_max_photochem_iterations = metadata_dict['input_max_photochem_iterations']
    point.temperature = metadata_dict['temperature']
    point.pressure = metadata_dict['pressure']
    session.commit()
    return "completed: %s - %s" % (point.hash, run_status)


def delete_db(data, dtype="dict"):
    if dtype == "dict":
        hashed = utilities.param_hash(data)
    elif dtype == "code":
        dicted = utilities.param_decode(data)
        hashed = utilities.param_hash(dicted)
    else:
        return "didn't recognize 'dtype'"
    point = session.query(ParameterSpace).filter_by(hash=hashed).first()
    session.delete(point)
    session.commit()
    return "deleted: %s" % point.hash

def exists_db(data, dtype="dict"):
    if dtype == "dict":
        hashed = utilities.param_hash(data)
    elif dtype == "code":
        dicted = utilities.param_decode(data)
        hashed = utilities.param_hash(dicted)
    else:
        return "didn't recognize 'dtype'"
    ret = session.query(exists().where(ParameterSpace.hash==hashed)).scalar()
    return ret



####################
### Pull items from Redis Queue for Read + Write

q = rediswq.RedisWQ(name=REDIS_SERVER_NAME, host=REDIS_SERVER_IP)
# ^consider making ^decode_responses=True^ so
# that we don't have to convert binary to unicode for getting items off list
if not args.master:
    print("Created Normal Write SQL Client")
    while not q.kill():

        param_code = q.get("run", block=True, timeout=30)
        if param_code is not None:
            msg = run_db(data=param_code, dtype="code")
            print(msg)
        else:
            pass

        packed_code = q.get("complete", block=True, timeout=30)
        if packed_code is not None:
            unpacked_list = utilities.unpack_items(packed_code)
            param_code = unpacked_list[0]

            atmos_output = unpacked_list[1]
            stable_atmosphere = unpacked_list[2]
            metadata_dict = utilities.metadata_decode(unpacked_list[3])
            msg = complete_db(data=param_code,
                            dtype="code",
                            run_status=atmos_output,
                            stability=stable_atmosphere,
                            metadata_dict=metadata_dict)
            print(msg)
        else:
            pass


        """
        param_code = q.get("error", block=True, timeout=15)
        if param_code is not None:
            msg = error_db(msg="std error", data=param_code, dtype="code")
            print(msg)
        else:
            pass

        param_code = q.get("complete0", block=True, timeout=15)
        if param_code is not None:
            msg = complete_db(msg="unstable", data=param_code, dtype="code")
            print(msg)
        else:
            pass

        param_code = q.get("complete1", block=True, timeout=15)
        if param_code is not None:
            msg = complete_db(msg="stable", data=param_code, dtype="code")
            print(msg)
        else:
            pass"""


else: #master True
    print("Created Master Read/Write SQL Client")
    while not q.kill():
        if q.size("complete")+q.size("run")+q.size("main sql")+q.size("main") == 0:
            points = session.query(ParameterSpace).filter_by(state='running')
            for point in points:
                timedelta = datetime.utcnow() - point.session_start_time
                timedelta = timedelta.days * 24 * 3600 + timedelta.seconds
                if timedelta > MAX_JOB_RUN_TIME:
                    #add points back to queue
                    print("re-queueing: %s - was on for %d seconds" % (point.hash, timedelta))
                    point.state = "queue"
                    point.session_start_time = datetime.utcnow()
                    session.commit()
                    q.put(point.code, "main")
                else:
                    pass
        else:
            pass

        param_code = q.get("main sql", block=True, timeout=30)
        if param_code is not None:
            next_param_code, prev_param_code = utilities.unpack_items(param_code)
            if not exists_db(next_param_code, dtype="code"): #check if item in DB already
                msg = add_db(data=next_param_code, dtype="code")
                q.put(param_code, "main")
                print(msg)
            else:
                # already in the DB
                print("repeat: %s" % utilities.param_hash(utilities.param_decode(next_param_code)))
                pass
        else:
            pass


