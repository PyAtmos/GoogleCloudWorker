import time
import rediswq
import utilities
from start import start 
from sql_client import *



increment_dict = {}


# add 'start' to the sql db
ret = add_db(start)

# add 'start' to task_queue
q = rediswq.RedisWQ(name="job2", host=utilities.redis_host)
q.put(value=param_str_enc(start), queue="main sql")
