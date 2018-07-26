import rediswq

q = rediswq.RedisWQ(name=REDIS_SERVER_NAME, host=REDIS_SERVER_IP)
while not q.kill():
    if q.size("main") != 0:
        item = q.get("main")
        if item is not None:
            q.put(value=item, queue="run")
