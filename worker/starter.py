import time
import rediswq
import utilities
from sql_create import *


start = {
	"02" : 0.05,
	"H2" : 0.20,
	"other" : 0.50,
	"filler" : 0.25
	}

increment_dict = {}


# add 'start' to the sql db
ret = add_db(start)

# add 'start' to task_queue
q = rediswq.RedisWQ(name="job2", host=utilities.redis_host)
q.put(value=param_str_enc(start), queue="main sql")
