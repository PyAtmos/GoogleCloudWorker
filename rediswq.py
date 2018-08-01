#!/usr/bin/env python

# SOURCE:
#https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/

# this is a huge frankenstein's monster of messy original^ code with rodd's hacks added in

####################################################################################################
# PACKAGES
import redis
import uuid
import hashlib

class RedisWQ(object):
    """Simple Finite Work Queue with Redis Backend

    This work queue is finite: as long as no more work is added
    after workers start, the workers can detect when the queue
    is completely empty.

    The items in the work queue are assumed to have unique values.

    This object is not intended to be used by multiple threads
    concurrently.
    """
    def __init__(self, name, **redis_kwargs):
       """The default connection parameters are: host='localhost', port=6379, db=0

       The work queue is identified by "name".  The library may create other
       keys with "name" as a prefix. 
       """
       self._db = redis.StrictRedis(**redis_kwargs)
       # The session ID will uniquely identify this "worker".
       self._session = str(uuid.uuid4())
       # Work queue is implemented as two queues: main, and processing.
       # Work is initially in main, and moved to processing when a client picks it up.
       self._main_q_key = name
       self._main_sql_q_key = name + ":sql:queue"

       self._processing_q_key = name + ":processing"
       self._lease_key_prefix = name + ":leased_by_session:"

       self._running_sql_q_key = name + ":sql:running"
       self._complete_sql_q_key = name + ":sql:complete"
       #self._error_sql_q_key = name + ":sql:error"
       #self._complete0_sql_q_key = name + ":sql:complete0"
       #self._complete1_sql_q_key = name + ":sql:complete1"

       self._kill_q_key = name + ":kill"

    def sessionID(self):
        """Return the ID for this session."""
        return self._session

    def _main_qsize(self):
        """Return the size of the main queue."""
        return self._db.llen(self._main_q_key)

    def _processing_qsize(self):
        """Return the size of the main queue."""
        return self._db.llen(self._processing_q_key)

    # rodd added:
    def size(self, q):
        if q == "main":
            return self._db.llen(self._main_q_key)
        elif q == "main sql":
            return self._db.llen(self._main_sql_q_key)
        elif q == "run":
            return self._db.llen(self._running_sql_q_key)
        elif q == "complete":
            return self._db.llen(self._complete_sql_q_key)
        #elif q == "error":
        #    return self._db.llen(self._error_sql_q_key)
        #elif q == "complete0":
        #    return self._db.llen(self._complete0_sql_q_key)
        #elif q == "complete1":
        #    return self._db.llen(self._complete1_sql_q_key)
        #elif q == "kill":
        #    return self._db.llen(self._kill_q_key)
        else:
            # incorrect q list/key given
            return None

    # rodd added:
    def _kill_switch(self):
        self._db.lpush(self._kill_q_key, "1")

    # rodd added:
    def kill(self):
        return self._db.llen(self._kill_q_key) > 0

    def empty(self):
        """Return True if the queue is empty, including work being done, False otherwise.

        False does not necessarily mean that there is work available to work on right now,
        """
        return self._main_qsize() == 0 and self._processing_qsize() == 0

# TODO: implement this
#    def check_expired_leases(self):
#        """Return to the work queueReturn True if the queue is empty, False otherwise."""
#        # Processing list should not be _too_ long since it is approximately as long
#        # as the number of active and recently active workers.
#        processing = self._db.lrange(self._processing_q_key, 0, -1)
#        for item in processing:
#          # If the lease key is not present for an item (it expired or was 
#          # never created because the client crashed before creating it)
#          # then move the item back to the main queue so others can work on it.
#          if not self._lease_exists(item):
#            TODO: transactionally move the key from processing queue to
#            to main queue, while detecting if a new lease is created
#            or if either queue is modified.

    def _itemkey(self, item):
        """Returns a string that uniquely identifies an item (bytes)."""
        return hashlib.sha224(item).hexdigest()

    def _lease_exists(self, item):
        """True if a lease on 'item' exists."""
        return self._db.exists(self._lease_key_prefix + self._itemkey(item))

    def to_queue(self):
        item = self._db.rpoplpush(self._main_sql_q_key, self._main_q_key)
        return item

    def buy(self, block=True, timeout=None):
        """Lite version of lease() that eliminates the actual 'lease' list.
        Right now, the sql_client already checks for 'running' jobs that never 
        seems to finish and adds those back into the queue so we don't need a lease list"""
        if block:
            item = self._db.brpoplpush(self._main_q_key, self._processing_q_key, timeout=timeout)
        else:
            item = self._db.rpoplpush(self._main_q_key, self._processing_q_key)

        if (item is not None) & (type(item)==bytes):
            item = str(item.decode("utf=8"))
        else:
            pass
        return item

    def lease(self, lease_secs=60, block=True, timeout=None):
        """Begin working on an item the work queue. 

        Lease the item for lease_secs.  After that time, other
        workers may consider this client to have crashed or stalled
        and pick up the item instead.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self._db.brpoplpush(self._main_q_key, self._processing_q_key, timeout=timeout)
        else:
            item = self._db.rpoplpush(self._main_q_key, self._processing_q_key)
        if item is not None:
            # Record that we (this session id) are working on a key.  Expire that
            # note after the lease timeout.
            # Note: if we crash at this line of the program, then GC will see no lease
            # for this item a later return it to the main queue.
            itemkey = self._itemkey(item)
            self._db.setex(self._lease_key_prefix + itemkey, lease_secs, self._session)
        return item

    # rodd added:
    def put(self, value, queue):
        """attempt to add a value to the main task queue"""
        if queue == "main":
            self._db.lpush(self._main_q_key, value)
        elif queue == "main sql":
            self._db.lpush(self._main_sql_q_key, value)
        elif queue == "run":
            self._db.lpush(self._running_sql_q_key, value)
        elif queue == "complete":
            self._db.lpush(self._complete_sql_q_key, value)
        #elif queue == "error":
        #    self._db.lpush(self._error_sql_q_key, value)
        #elif queue == "complete0":
        #    self._db.lpush(self._complete0_sql_q_key, value)
        #elif queue == "complete1":
        #    self._db.lpush(self._complete1_sql_q_key, value)
        else:
            # incorrect queue given
            pass

    # rodd added:
    def get(self, queue, block=False, timeout=None):
        if block:
            if queue == "main":
                item = self._db.brpop(self._main_q_key, timeout)
            elif queue == "main sql":
                item = self._db.brpop(self._main_sql_q_key, timeout)
            elif queue == "run":
                item = self._db.brpop(self._running_sql_q_key, timeout)
            elif queue == "complete":
                item = self._db.brpop(self._complete_sql_q_key, timeout)
            #elif queue == "error":
            #    item = self._db.brpop(self._error_sql_q_key, timeout)
            #elif queue == "complete0":
            #    item = self._db.brpop(self._complete0_sql_q_key, timeout)
            #elif queue == "complete1":
            #    item = self._db.brpop(self._complete1_sql_q_key, timeout)
            else:
                print("ERROR: not a proper queue name")
                return 0
            if item is not None:
                item = item[1] #brpop returns a tuple : (list id, value)
            else:
                pass #item is None
        else:
            if queue == "main":
                item = self._db.rpop(self._main_q_key)
            elif queue == "main sql":
                item = self._db.rpop(self._main_sql_q_key)
            elif queue == "run":
                item = self._db.rpop(self._running_sql_q_key)
            elif queue == "complete":
                item = self._db.rpop(self._complete_sql_q_key)
            #elif queue == "error":
            #    item = self._db.rpop(self._error_sql_q_key)
            #elif queue == "complete0":
            #    item = self._db.rpop(self._complete0_sql_q_key)
            #elif queue == "complete1":
            #    item = self._db.rpop(self._complete1_sql_q_key)
            else:
                print("ERROR: not a proper queue name")
                return 0
        if (item is not None) & (type(item)==bytes):
            item = str(item.decode("utf=8")) #python2 .decode(...) outputs unicde, python3 outputs str
        else:
            pass
        return item

    def complete(self, value):
        """Complete working on the item with 'value'.

        If the lease expired, the item may not have completed, and some
        other worker may have picked it up.  There is no indication
        of what happened.
        """
        self._db.lrem(self._processing_q_key, 0, value)
        # If we crash here, then the GC code will try to move the value, but it will
        # not be here, which is fine.  So this does not need to be a transaction.
        #itemkey = self._itemkey(value)
        #self._db.delete(self._lease_key_prefix + itemkey, self._session)

# TODO: add functions to clean up all keys associated with "name" when
# processing is complete.

# TODO: add a function to add an item to the queue.  Atomically
# check if the queue is empty and if so fail to add the item
# since other workers might think work is done and be in the process
# of exiting.

# TODO(etune): move to my own github for hosting, e.g. github.com/erictune/rediswq-py and
# make it so it can be pip installed by anyone (see
# http://stackoverflow.com/questions/8247605/configuring-so-that-pip-install-can-work-from-github)

# TODO(etune): finish code to GC expired leases, and call periodically
#  e.g. each time lease times out.
