# Source:
#https://github.com/GoogleCloudPlatform/getting-started-python/blob/master/2-structured-data/bookshelf/model_cloudsql.py
# And:
#https://cloud.google.com/python/getting-started/using-cloud-sql

####################################################################################################
from starter import start

#from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# not sure how much of this is needed...just dump all
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import exists, filter_by

####################
### Quick Ftn
def param_str_enc(platform_dict):
    platform_str = ""
    for molecule, _ in start.items():
        #string += molecule
        concentration = platform_dict[molecule]
        platform_str += str(concentration)
        platform_str += ","
    platform_str = platform_str[-1] #remove trailing comma
    return platform_str

def param_str_dec(platform_str):
    platform_list = platform_str.split(",")
    platform_dict = {}
    for i, (molecule,_) in enumerate(start.items()):
        platform_dict[molecule] = platform_list[i]
    return platform_dict

def param_hash(platform):
    if type(platform) is dict:
        string = param_str(platform)
    elif type(platform) is str:
        string = platform
    else:
        print("ERROR: platform in param_hash() not a string or dict")
        return 0
    hash_object = hashlib.md5(str.encode(string))
    return hash_object.hexdigest()


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
    run_time = Column(DateTime)
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

def add_db(data):
    # data is parameter_dict
    # Insert a Person in the person table
    point = ParameterSpace(data)
    session.add(point)
    session.commit()
    return "added to db: %s" % point.hash

def run_db(data=None, hash=None):
    if data is not None:
        hashed = hash_param(data)
    point = session.query(ParameterSpace).filter_by(hash=hashed).first()
    point.state = "Running"
    point.start_time = datetime.utcnow()
    session.commit()
    return "running %s" % point.hash

def error_db(msg, data=None, hash=None):
    if data is not None:
        hashed = hash_param(data)
    point = session.query(ParameterSpace).filter_by(hash=hashed).first()
    point.state = "Error"
    point.error_msg = str(msg) #<-exapnd on this
    point.run_time = datetime.utcnow() - point.start_time #<-fix this
    session.commit()
    return "%s errored: %s" % (point.hash, msg)

def complete_db(msg, data=None, hash=None):
    if data is not None:
        hashed = hash_param(data)
    point = session.query(ParameterSpace).filter_by(hash=hashed).first()
    point.state = "Complete"
    point.complete_msg = str(msg) #<-exapnd on this
    point.run_time = datetime.utcnow() - point.start_time #<-fix this
    session.commit()
    return "%s completed: %s" % (point.hash, msg)


def delete_db(data=None, hash=None):
    if data is not None:
        hashed = hash_param(data)
    point = session.query(ParameterSpace).filter_by(hash=hashed).first()
    session.delete(point)
    session.commit()
    return "deleted %s" % point.hash

def exists_db(data=None, hash=None):
    if data is not None:
        hashed = hash_param(data)
    ret = session.query(exists().where(ParameterSpace.hash==hashed)).scalar()
    return ret
