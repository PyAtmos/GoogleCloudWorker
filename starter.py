import rediswq
import utilities
from config import *


# add 'start' to task_queue
q = rediswq.RedisWQ(name=REDIS_SERVER_NAME, host=REDIS_SERVER_IP)
packed_items = utilities.pack_items( [utilities.param_encode(start), "first run"] )
q.put(value=packed_items, queue="main sql")