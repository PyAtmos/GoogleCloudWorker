# utility file for keeping consistent language in handling parameters

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

def param_hash(platform_dict):
    if type(platform_dict) is dict:
        string = param_str(platform)
    elif type(platform_dict) is str:
        string = platform_dict
    else:
        print("ERROR: platform in param_hash() not a string or dict")
        return 0
    hash_object = hashlib.md5(str.encode(string))
    return hash_object.hexdigest()