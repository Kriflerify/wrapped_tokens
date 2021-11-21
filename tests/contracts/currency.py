__balances = Hash(default_value=0, contract='currency', name='balances')


def ____(vk: str):
    __balances[vk] = 288090567


@__export('currency')
def transfer(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    sender = ctx.caller
    assert __balances[sender] >= amount, 'Not enough coins to send!'
    __balances[sender] -= amount
    __balances[to] += amount


@__export('currency')
def balance_of(account: str):
    return __balances[account]


@__export('currency')
def allowance(owner: str, spender: str):
    return __balances[owner, spender]


@__export('currency')
def approve(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    sender = ctx.caller
    __balances[sender, to] += amount
    return __balances[sender, to]


@__export('currency')
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, 'Cannot send negative balances!'
    sender = ctx.caller
    assert __balances[main_account, sender
        ] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'.format(
        __balances[main_account, sender], amount)
    assert __balances[main_account] >= amount, 'Not enough coins to send!'
    __balances[main_account, sender] -= amount
    __balances[main_account] -= amount
    __balances[to] += amount

