# python script to do a tracked kill or quick kill of all servers

import rediswq
import argparse

import time

#####
parser = argparse.ArgumentParser(description='Grab Kill-type flag')
parser.add_argument('-k', '--killquick', type=int, default=False,
                    help='switch to do a quick kill or track a reason to kill')
parser.add_argument('-f', '--forgive_threshold', type=int, default=1,
                    help='max number of times in a row that you forgive for getting a reason to kill')
args = parser.parse_args()


q = rediswq.RedisWQ(name="job2", host=utilities.redis_host)

if args.killquick:
    # add to the redis q for kill
    q._kill_switch()
    # done

else:
    # track for a reason to kill
    empty = 0
    while empty > forgive_threshold:
        if q.size("main")+q.size("complete1") == 0:
            empty += 1
            time.sleep(60*5) #5min
        else:
            # we got stuff to do and let's reset count!
            empty = 0
    # if we're here, then we're out of the loop...Kill
    q._kill_switch()
    # done