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
    __tablename__ = 'parameterspace'
    id = Column(Integer, primary_key=True)
    hash = Column(String(256))
    code = String(256)
    H2 = Column(Float)
    O2 = Column(Float)
    #...
    state = Column(String(256))
    start_time = Column(DateTime)
    error_msg = Column(String(256))
    complete_msg = Column(String(256))
    end_time = Column(DateTime)
    out_path = Column(String(256))
    #
    def __init__(self, parameter_dict):
        self.hash = utilities.param_hash(parameter_dict)
        self.code = utilities.param_encode(parameter_dict)
        self.H2 = parameter_dict['H2']
        self.O2 = parameter_dict['O2']
        #...
        self.state = "Queue"
        self.start_time = datetime.utcnow()

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
    point.state = "Running"
    point.start_time = datetime.utcnow()
    session.commit()
    return "running: %s" % point.hash

def error_db(msg, data, dtype="dict"):
    if dtype == "dict":
        hashed = utilities.param_hash(data)
    elif dtype == "code":
        dicted = utilities.param_decode(data)
        hashed = utilities.param_hash(dicted)
    else:
        return "didn't recognize 'dtype'"
    point = session.query(ParameterSpace).filter_by(hash=hashed).first()
    point.state = "Error"
    point.error_msg = str(msg) #<-exapnd on this
    point.end_time = datetime.utcnow()
    session.commit()
    return "errored: %s - %s" % (point.hash, msg)

def complete_db(msg, data, dtype="dict"):
    if dtype == "dict":
        hashed = utilities.param_hash(data)
    elif dtype == "code":
        dicted = utilities.param_decode(data)
        hashed = utilities.param_hash(dicted)
    else:
        return "didn't recognize 'dtype'"
    point = session.query(ParameterSpace).filter_by(hash=hashed).first()
    point.state = "Complete"
    point.complete_msg = str(msg) #<-exapnd on this
    point.end_time = datetime.utcnow()
    session.commit()
    return "completed: %s - %s" % (point.hash, msg)


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
    print("Created normal SQL Client")
    while not q.kill():
        if q.size("run")+q.size("error")+q.size("complete0") == 0:
            ##########
            #FUTURE WORK
            # if all queues are empty; look up sql table to see how many are state='running'
            # and see how long they have been running...
            # if running for 'too long', then assume that the node died mid-run; change state to queue and add to "main"
            ##########
            time.sleep(5) # kill time
        else:
            pass

        if q.size("run") != 0:
            item = q.get("run")
            if item:
                param_code = item#.decode("utf=8")
                msg = run_db(data=param_code, dtype="code")
                print(msg)
            else:
                pass
        else:
            pass
        if q.size("error") != 0:
            item = q.get("error")
            if item:
                param_code = item#.decode("utf=8")
                msg = error_db(msg="unknown", data=param_code, dtype="code")
                print(msg)
                #q.complete(item)
            else:
                pass
        else:
            pass
        if q.size("complete0"):
            item = q.get("complete0")
            if item:
                param_code = item#.decode("utf=8")
                msg = complete_db(msg="unstable", data=param_code, dtype="code")
                print(msg)
            else:
                pass
        else:
            pass


else: #master True
    print("Created Master Client")
    while not q.kill():
        if q.size("complete1")+q.size("main sql") == 0:
            if q.size("main") == 0:
                points = session.query(ParameterSpace).filter_by(state='running')
                for point in points:
                    timedelta = datetime.utcnow() - point.start_time
                    timedelta = timedelta.days * 24 * 3600 + timedelta.seconds
                    if timedelta > MAX_JOB_RUN_TIME:
                        #add points back to queue
                        point.state = "Queue"
                        point.start_time = datetime.utcnow()
                        q.put(point.code, "main")
                        session.commit()
                    else:
                        pass
            else:
                pass
            time.sleep(5) # kill time
        else:
            pass
        if q.size("complete1") != 0:
            item = q.get("complete1")
            if item:
                param_code = item#.decode("utf=8")
                msg = complete_db(msg="stable", data=param_code, dtype="code")
                print(msg)
                '''
                param_dict = utilities.param_decode(param_code)
                utilities.explore(
                    param_dict=param_dict,
                    increment_dict=increment_dict,
                    redis_db=q,
                    step_Size=2,
                    search_mode="sides")'''
            else:
                pass
        else:
            pass
        for _ in range(2*(len(ALTER_MOLECULES)-2)): #...one for each direction and molecule
            if q.size("main sql") != 0:
                item = q.get("main sql")
                if item:
                    param_code = item#.decode("utf=8")
                    if not exists_db(param_code, dtype="code"):#check if item in DB already
                        msg = add_db(data=param_code, dtype="code")
                        q.put(param_code, "main")
                        print(msg)
                    else:
                        # already in the DB
                        pass
                else:
                    pass
            else:
                break

