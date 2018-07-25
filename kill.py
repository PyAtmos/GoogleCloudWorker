# python script to do a tracked kill or quick kill of all servers

####################################################################################################
# PACKAGES
import argparse
import time

# SCRIPTS
import rediswq
from config import *


####################
### Input arguments
parser = argparse.ArgumentParser(description='Grab Kill-type flag')
parser.add_argument('-k', '--killquick', type=int, default=False,
                    help='switch to do a quick kill or track a reason to kill')
parser.add_argument('-f', '--forgive_threshold', type=int, default=1,
                    help='max number of times in a row that you forgive for getting a reason to kill')
parser.add_argument('-r', '--reset', type=int, default=False,
                    help='switch to only reset kill queue to 0')
args = parser.parse_args()



####################
### Connect to Redis Server
q = rediswq.RedisWQ(name=REDIS_SERVER_NAME, host=REDIS_SERVER_IP)


####################
### Reset Kill Queue to 0
if args.reset:
    #item = q._db.rpop(q._kill_q_key)
    q._db.flushdb() #Delete all keys in the current database
    print("Deleted all keys in the current database...")
    exit()
else:
    pass


####################
### Pull items from Redis Queue for Read + Write
if args.killquick:
    # add to the redis q for kill
    q._kill_switch()
    print("Sent signal to all servers to turn off")
else:
    # track for a reason to kill
    empty_count = 0
    wait_minutes = 5
    print("Watching for empty queues...")
    while empty_count > forgive_threshold:
        if q.size("main")+q.size("complete1") == 0:
            empty_count += 1
            print("This is the %d time that we found empty queues\n...sleeping for %dmin before checking again" % (empty_count, wait_minutes)
            time.sleep(60*wait_minutes)
        else:
            # we got stuff to do so let's reset count!
            empty_count = 0
            print("Queues filled...resetting count")
    # if we're here, then we're out of the loop...Kill
    q._kill_switch()
    print("Queues left empty for too long\n...Sent signal to all servers to turn off")

