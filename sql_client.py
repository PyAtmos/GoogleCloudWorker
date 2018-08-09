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
from sqlalchemy.sql import exists

####################
### Input arguments
parser = argparse.ArgumentParser(description='Grab Master flag')
parser.add_argument('-m', '--main', type=int, default=False,
                    help='if nonzero, it strictly deals with adding items from main-sql to main queue')
parser.add_argument('-r', '--run', type=int, default=False,
                    help='if nonzero, it strictly deals with grabbing items from run queue')
# ^'run' phased out...see closed issue on GitHub
parser.add_argument('-c', '--complete', type=int, default=False,
                    help='if nonzero, it strictly deals with grabbing items from complete queue')
parser.add_argument('-R', '--reset', type=int, default=False,
                    help='if nonzero, delete existing tables and create new')
parser.add_argument('-C', '--create', type=int, default=False,
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
    previous_hash = Column(String(256))
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
    atmos_run_duration = Column(String(256))
    run_iteration_call = Column(String(256))
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
    hashed = point.hash
    session.add(point)
    session.commit()

    # check that the point now exists
    forgive = 0
    while forgive < 5:
        ret = session.query(exists().where(ParameterSpace.hash==hashed)).scalar()
        if not ret:
            forgive += 1
            time.sleep(5)
        else:
            break
    if not ret:
        return "tried to add; couldn't find [%s] in database table" % (hashed)
    else:
        pass
    return "added: %s" % point.hash

def run_db(data, dtype="dict"):
    if dtype == "dict":
        hashed = utilities.param_hash(data)
    elif dtype == "code":
        dicted = utilities.param_decode(data)
        hashed = utilities.param_hash(dicted)
    else:
        return "didn't recognize 'dtype'"
    forgive = 0
    while forgive < 5: #add forgiveness buffer to make sure it has the time to get added to sql db
        point = session.query(ParameterSpace).filter_by(hash=hashed).first()
        if point is None:
            forgive += 1
            time.sleep(5)
        else:
            break
    if point is None:
        return "tried to run; couldn't find [%s] in database table" % (hashed)
    else:
        pass
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
    forgive = 0
    while forgive < 5: #add forgiveness buffer to make sure it has the time to get added to sql db
        point = session.query(ParameterSpace).filter_by(hash=hashed).first()
        if point is None:
            forgive += 1
            time.sleep(5)
        else:
            break
    if point is None:
        return "tried to complete; couldn't find [%s] in database table" % (hashed)
    else:
        pass
    point.state = run_status
    point.stable = stability
    point.session_end_time = datetime.utcnow()
    point.bucket_path = JOB_STORAGE_PATH
    # metadata
    # session.commit doesn't acknowledge changes like this: point.__dict__[key] = metadata_dict[key]
    # so hard code the updates for each attribute
    point.previous_hash = metadata_dict['previous_hash']
    point.run_iteration_call = metadata_dict['run_iteration_call']
    point.atmos_start_time = metadata_dict['atmos_start_time']
    point.photochem_duration = metadata_dict['photochem_duration']
    point.photochem_iterations = metadata_dict['photochem_iterations']
    point.clima_duration = metadata_dict['clima_duration']
    point.atmos_run_duration = metadata_dict['atmos_run_duration']
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

# default to main if nothing else:
if (not args.run) and (not args.complete):
    args.main = True
else:
    pass

if args.complete:
    print("Created Write SQL Client for 'Complete Queue'")
    while not q.kill():

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
            if msg[:5] == "tried":
                # failed to add, add back to queue
                q.put(value=packed_code, queue="complete")
            else:
                pass

        else:
            pass

elif args.main: #master True
    print("Created Read/Write SQL Client for 'Main Queue'")
    
    checkpoint_time = time.time()
    while not q.kill():
        #if q.size("complete")+q.size("run")+q.size("main sql")+q.size("main") == 0:
        # instead, check every .25hour
        if time.time() >= checkpoint_time + 1.0*60*60:
            points = session.query(ParameterSpace).filter_by(state='queue')
            for point in points:
                timedelta = datetime.utcnow() - point.session_start_time
                timedelta = timedelta.days * 24 * 3600 + timedelta.seconds
                if timedelta > MAX_JOB_QUEUE_TIME:
                    #add points back to queue
                    print("re-queueing: %s - was on for %d seconds" % (point.hash, timedelta))
                    point.state = "queue"
                    point.session_start_time = datetime.utcnow()
                    session.commit()
                    packed_items = utilities.pack_items( [point.code, point.previous_hash] )
                    q.put(packed_items, "main")
                else:
                    pass
            checkpoint_time = time.time()
        else:
            pass

        packed_items = q.get("main sql", block=True, timeout=30)
        if packed_items is not None:
            next_param_code, prev_param_hash, explore_count = utilities.unpack_items(packed_items)
            if not exists_db(next_param_code, dtype="code"): #check if item in DB already
                explore_count = 0
                packed_items = utilities.pack_items( [next_param_code, prev_param_hash, explore_count] )
                msg = add_db(data=next_param_code, dtype="code")
                q.put(packed_items, "main")
                print(msg)
            else:
                # already in the DB...check if it also completed
                dicted = utilities.param_decode(next_param_code)
                hashed = utilities.param_hash(dicted)
                point = session.query(ParameterSpace).filter_by(hash=hashed).first()
                if point.temperature is None: # didn't complete, ignore
                    print("repeat: %s" % hashed)
                    pass
                elif explore_count < EXPLORE_LIMIT: #did complete, and didn't already pass limit
                    explore_count += 1
                    # add point to queue only so it explores
                    packed_items = utilities.pack_items( [next_param_code, "explore only", explore_count] )
                    q.put(packed_items, "main")
                    print("re-explore: %s" % hashed)
                else: #did complete, but passed limit
                    pass
        else:
            pass

''' # removed because the sql server didn't update fast enough...see issue on GitHub
elif args.run:
    print("Created Write SQL Client for 'Run Queue'")
    while not q.kill():

        param_code = q.get("run", block=True, timeout=30)
        if param_code is not None:
            msg = run_db(data=param_code, dtype="code")
            print(msg)
        else:
            pass
'''

else:
    pass


