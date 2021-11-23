from contracting.execution.runtime import rt
from contracting.stdlib import env
from contracting import config
from contracting import client
import pdb

from random import randbytes

# We need to import "currency" but only have compiled code (obtained from lamden masternodes).
# client.submit only allows compiled code, so try to submit with 
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

def getKeys(client, contract_name, variable_name):
    contract = client.get_contract(contract_name)
    if contract:
        keys = contract.keys()
        raw_keys = [k[k.find(":")+1:] for k in keys if f"{contract_name}.{variable_name}" in k]
        return [k for k in raw_keys if ":" not in k]


def getAllHashValues(client, contract_name, variable_name):
    """Return a python dict with all key-value pairs stored in a given Hash object of a contract
    """
    keys = getKeys(client, contract_name, variable_name)
    if not keys:
        return {}
    contract = client.get_contract(contract_name)
    values = {}
    for a in keys:
        values[a] = contract.quick_read(variable=variable_name, key=a)
    return values

def randomEthAddress():
    return "0x" + randbytes(20).hex()