import rediswq
import utilities
from config import *

# add 'start' to the sql db
#ret = add_db(start)

# add 'start' to task_queue
q = rediswq.RedisWQ(name=REDIS_SERVER_NAME, host=REDIS_SERVER_IP)
q.put(value=utilities.param_encode(start), queue="main sql")
