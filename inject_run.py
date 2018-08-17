# new run...
import rediswq
import utilities
from config import *
from copy import deepcopy

# starting point for the search
start = {
    "O2" : 0.21,
    "N2" : 0.7772982887,
    "H2O" : 0.0123,
    "CH4" : 0.00000163,
    "CO2" : 0.0004,
    "H2" : 0.0000000813,
    }

# add 'start' to task_queue
q = rediswq.RedisWQ(name=REDIS_SERVER_NAME, host=REDIS_SERVER_IP)

new = deepcopy(start)
new['O2'] = 0.51
new['H2'] = 0.000000081
new["N2"] = utilities.calc_filler(new)
prev_hash = '4f9d1ccc79ef832b4446424fa00354f2'
packed_items = utilities.pack_items( [utilities.param_encode(new), prev_hash, "0"] )
q.put(value=packed_items, queue="main sql")


new = deepcopy(start)
new['H2'] = 0.000000078
new['H2O'] = 0.51
new["N2"] = utilities.calc_filler(new)
prev_hash = '64cd29732e7620a9a7e370d52d23e1c8'
packed_items = utilities.pack_items( [utilities.param_encode(new), prev_hash, "0"] )
q.put(value=packed_items, queue="main sql")




new = deepcopy(start)
new['CH4'] = 0.14
new["N2"] = utilities.calc_filler(new)
prev_hash = '0e55f9c33fb9c9cb1f49b149f7fea515'
packed_items = utilities.pack_items( [utilities.param_encode(new), prev_hash, "0"] )
q.put(value=packed_items, queue="main sql")




new = deepcopy(start)
new['CO2'] = 0.21
new["N2"] = utilities.calc_filler(new)
prev_hash = 'e4da48bc66dd82f8fa14a37a9e96a9a6'
packed_items = utilities.pack_items( [utilities.param_encode(new), prev_hash, "0"] )
q.put(value=packed_items, queue="main sql")



new = deepcopy(start)
new['H2'] = 0.2
new["N2"] = utilities.calc_filler(new)
prev_hash = '8db61283551affcbe2a3a2ea6d5f1aff'
packed_items = utilities.pack_items( [utilities.param_encode(new), prev_hash, "0"] )
q.put(value=packed_items, queue="main sql")




