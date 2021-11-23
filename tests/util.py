from contracting.execution.runtime import rt
from contracting.stdlib import env
from contracting import config
from contracting import client
import pdb

from random import randbytes

# We need to import "currency" but only have compiled code (obtained from lamden masternodes).
# client.submit only allows compiled code, so try to submit compiled code 
def submit_compiled(client, name, code_obj, owner=None, developer=None, args=None):
    """Submits compiled code of a contract.
    """
    scope = env.gather()
    scope.update({"__contract__": True})
    scope.update(rt.env)

    exec(code_obj, scope)

    if args:
        scope[config.INIT_FUNC_NAME](**args)
    else:
        scope[config.INIT_FUNC_NAME]()
    

    client.raw_driver.set_contract(name=name, code=code_obj, owner=owner,
        overwrite=False, developer=developer)


def tupleOrOne(list):
    # List should not have length 0
    if len(list)>1:
        return tuple(list)
    else:
        return list[0]

def getKeys(client, contract_name, variable_name, level=1):
    """Returns all keys of a hash. Each key is a list containing one or multiple elements
    depending on whether the key is from a multihash or not
    """
    contract = client.get_contract(contract_name)
    if contract:
        raw_keys = contract.keys()
        keys = []
        id = f"{contract_name}.{variable_name}"
        for k in raw_keys:
            if k[:len(id)]==id and k.count(":")==level:
                key_name = k[k.find(":")+1:]
                key = key_name.split(":")
                keys.append(key)
        return keys


def getAllHashValues(client, contract_name, variable_name, level=1):
    """Return a python dict with all key-value pairs stored in a given Hash object of a contract.
    Level=1 will return all hashes with single value key, eg. balances[key1]
    level=2 will return all hashes with two value key, e.g. balances[key1, key2]
    etc.
    """
    keys = getKeys(client, contract_name, variable_name, level)
    if not keys:
        return {}
    contract = client.get_contract(contract_name)
    values = {}
    for a in keys:
        values[tupleOrOne(a)] = client.get_var(contract_name, variable_name, arguments=a)
    return values

def randomEthAddress():
    return "0x" + randbytes(20).hex()