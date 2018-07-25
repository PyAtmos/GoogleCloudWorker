# Source:
#https://github.com/GoogleCloudPlatform/getting-started-python/blob/master/2-structured-data/bookshelf/model_cloudsql.py
# And:
#https://cloud.google.com/python/getting-started/using-cloud-sql

####################################################################################################
from starter import start, increment_dict
import utilities
import rediswq
import argparse

#from flask_sqlalchemy import SQLAlchemy
import time
from datetime import datetime
# not sure how much of this is needed...just dump all
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import exists#, filter_by

#####
parser = argparse.ArgumentParser(description='Grab Master flag')
parser.add_argument('-m', '--master', type=int, default=False,
                    help='if nonzero, assigns node to do the "masters" work')
args = parser.parse_args()


####################
### Create SQL Table

Base = declarative_base()
# got the line bellow from...NOT SURE HOW TO CONFIG FOR OUR PURPOSE?
#https://slebiblog.wordpress.com/2017/05/08/first-blog-post/
dbFilePath = 'mysql+pymysql://root:ROOT_PASSWORD@/DATABASE_NAME?unix_socket=/cloudsql/CONNECTION_NAME'
engine = create_engine(dbFilePath, echo=False)
DBSession = sessionmaker(bind=engine)
session = DBSession()

class ParameterSpace(Base):
    __tablename__ = 'parameterspace'
    id = Column(Integer, primary_key=True)
    hash = Column(String(32))
    H2 = Column(Float)
    O2 = Column(Float)
    #...
    state = Column(String)
    start_time = Column(DateTime)
    error_msg = Column(String)
    complete_msg = Column(String)
    end_time = Column(DateTime)
    out_path = Column(String)
    #
    def __init__(self, parameter_dict):
        self.hash = param_hash(parameter_dict)
        self.H2 = parameter_dict['H2']
        self.O2 = parameter_dict['O2']
        #...
        self.state = "Queue"
        self.start_time = datetime.utcnow()

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)



####################
##### useful functions

def add_db(param_dict):
    # data is parameter_dict
    # Insert a Person in the person table
    point = ParameterSpace(param_dict)
    session.add(point)
    session.commit()
    return "added to db: %s" % point.hash

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
    return "running %s" % point.hash

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
    return "%s errored: %s" % (point.hash, msg)

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
    return "%s completed: %s" % (point.hash, msg)


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
    return "deleted %s" % point.hash

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
### Loop keeping an eye on Redis server

# SOURCE: for only the redis part
#https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/


q = rediswq.RedisWQ(name="job2", host=utilities.redis_host)
# ^consider making ^decode_responses=True^ so
# that we don't have to convert binary to unicode for getting items off list
if not args.master:
    # then search for main_sql, running_sql, error_sql, complete_unstalbe
    while not q.kill():
        if q.size("run")+q.size("error")+q.size("complete0") == 0:
            time.sleep(30) # kill time
        else:
            pass

        if q.size("run") != 0:
            item = q.get("run")
            param_code = item.decode("utf=8")
            run_db(data=param_code, dtype="code")
        else:
            pass
        if q.size("error") != 0:
            item = q.get("error")
            param_code = item.decode("utf=8")
            error_db(data=param_code, dtype="code")
            q.complete(item)
        else:
            pass
        if q.size("complete0"):
            item = q.get("complete0")
            param_code = item.decode("utf=8")
            complete_db(msg="UnStable", data=param_code, dtype="code")
            #q.complete(item)
        else:
            pass


else: #master True
    # then search for complete_sql
    while not q.kill():
        if q.size("complete1") != 0:
            item = q.get("complete1")
            param_code = item.decode("utf=8")
            complete_db(msg="Stable", data=param_code, dtype="code")
            #q.complete(item)
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
        for _ in range(2*(len(start)-2)): #...one for each direction and molecule
            if q.size("main sql") != 0:
                item = q.get("main sql") # .to_queue()
                param_code = item.decode("utf=8")
                if not exists_db(param_code, dtype="code"):#check if item in DB already
                    add_db(data=param_code, dtype="code")
                    q.put(param_code, "main")
                else:
                    # already in the DB
                    pass
            else:
                break














