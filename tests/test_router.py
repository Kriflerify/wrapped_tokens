#tests/test_router.py
import unittest
import pdb
from contracting.client import ContractingClient
from contracting.stdlib.bridge.hashing import sha3
from tests.util import getAllHashValues, randomEthAddress
from contracting.stdlib.bridge import decimal

client = ContractingClient()

# Necessary so that token contract allows router to mint
ROUTER_NAME = "con_clearing_house_62"


def calcBalances(client, token_name, transactions):
    balances = getAllHashValues(client, token_name, "balances")
    # pdb.set_trace()
    for k, v in balances.items():
        if type(v) != decimal.ContractingDecimal:
            balances[k] = decimal.ContractingDecimal(v)

    for account, amount in transactions.items():
        if type(amount) != decimal.ContractingDecimal:
            amount = decimal.ContractingDecimal(amount)
        if account in balances:
            balances[account] += amount
        else: 
            balances[account] = amount
    return balances

def calcBalanceAfterMint(client, token_name, case, decimals):
    amount = int(case["amount"], 16) / (10 ** decimals)
    account = case["lamden_wallet"]
    transactions = {account: amount}
    return calcBalances(client, token_name, transactions)

def calcBalancesAfterBurn(client, token_name, case):
    amount = case["amount"]
    account = case["lamden_address"]
    if type(amount)==str:
        transactions = {account: "-" + amount, ROUTER_NAME: amount}
    else:
        transactions = {account: -amount, ROUTER_NAME: amount}
    return calcBalances(client, token_name, transactions)

def incrementNonces(nonces, *accounts):
    for acc in accounts:
        if acc in nonces:
            nonces[acc] += 1
        else:
            nonces[acc] = 1
    return nonces

class TestRouter(unittest.TestCase):
    def setUp(self):
        self.c = client
        self.c.flush()

        with open("lamden/router.py") as f:
            code = f.read()
            self.c.submit(code, name=ROUTER_NAME)
            self.router = self.c.get_contract(ROUTER_NAME)    

        with open("lamden/token.py") as f:
            self.token_code = f.read()
            self.c.submit(self.token_code, "token1")
            self.token1 = self.c.get_contract("token1")


    def tearDown(self):
        self.c.flush()


    def test_mint(self):
        ETH_TOKEN1 = randomEthAddress() # for well suited token
        ETH_TOKEN2 = randomEthAddress() # for well suited token
        ETH_TOKEN3 = randomEthAddress() # for unregistered token
        ETH_TOKEN4 = randomEthAddress() # for token with decimal=None

        # If a dict has a 'add_token' key, the contracts are flushed, resubmitted and the 
        # token (as described by the correspoding value of key 'add_token') is resubmitted and added 
        # If a dict does not have an 'add_token' key, the contracts from previous tests are used
        #
        # lamden_contract is constantly token1 because it is assumed that add_token would not
        # allow to submit a contract that does not enforce the token contract 
        test_cases=[
            {"add_token": 
                {"ethereum_contract": ETH_TOKEN1 , "lamden_contract": "token1", "decimals": 18},
            "mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN1, "amount": "0x10",
                    "lamden_wallet": "user"}},
            {"mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN1, "amount": "10",
                "lamden_wallet": "user"}},
            {"mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN1, "amount": "0x10",
                "lamden_wallet": ROUTER_NAME}},
            {"add_token": 
                {"ethereum_contract": ETH_TOKEN2, "lamden_contract": "token1", "decimals": 0},
            "mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN2, "amount": "10",
                "lamden_wallet": "user"}},
            {"mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN2, "amount": "10",
                "lamden_wallet": self.c.signer}},
            {"mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN2, "amount": "10",
                "lamden_wallet": ROUTER_NAME}},
        ]

        fail_cases=[
            # impossible amount
            {"add_token": 
                {"ethereum_contract": ETH_TOKEN1 , "lamden_contract": "token1", "decimals": 18},
            "mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN1, "amount": "text",
                "lamden_wallet": "user"},
            "msg":
                "Impossible amount could be minted"},
            {"mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN1, "amount": "-0x14",
                "lamden_wallet": "user"},
            "msg":
                "Impossible amount could be minted"},
            {"mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN1, "amount": "",
                "lamden_wallet": "user"},
            "msg":
                "Impossible amount could be minted"},
            {"mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN1, "amount": None,
                "lamden_wallet": "user"},
            "msg":
                "Impossible amount could be minted"},

            # Non-onwer trying to mint
            {"mint":
                {"signer": "foreigner", "ethereum_contract": ETH_TOKEN1, "amount": "0x14",
                "lamden_wallet": "user"},
            "msg":
                "Non-owner is able to mint, but shouldn't"},
            {"mint":
                {"signer": "user", "ethereum_contract": ETH_TOKEN1, "amount": "0x14",
                "lamden_wallet": "user"},
            "msg":
                "Non-owner is able to mint, but shouldn't"},
            {"mint":
                {"signer": "user", "ethereum_contract": ETH_TOKEN1, "amount": "0x14",
                "lamden_wallet": self.c.signer},
            "msg":
                "Non-owner is able to mint, but shouldn't"},
            {"mint":
                {"signer": "user", "ethereum_contract": ETH_TOKEN1, "amount": "0x14",
                    "lamden_wallet": ROUTER_NAME},
            "msg":
                "Non-owner is able to mint, but shouldn't"},
            {"mint":
                {"signer": "user", "ethereum_contract": ETH_TOKEN1, "amount": "0x14",
                    "lamden_wallet": None},
            "msg":
                "Non-owner is able to mint, but shouldn't"},

            # Unregistered ethereum token
            {"mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN3, "amount": "0x14",
                "lamden_wallet": "user"},
            "msg":
                "An unsupported ethereum token was able to be minted"},
            {"mint":
                {"signer": self.c.signer, "ethereum_contract": None, "amount": "0x14",
                "lamden_wallet": "user"},
            "msg":
                "An unsupported ethereum token was able to be minted"},
            {"add_token": 
                    {"ethereum_contract": ETH_TOKEN1, "lamden_contract": "token1", "decimals": 18},
            "mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN3, "amount": "0x14",
                "lamden_wallet": "user"},
            "msg":
                "An unsupported ethereum token was able to be minted"},

            # bad decimals
            {"add_token": 
                {"ethereum_contract": ETH_TOKEN4, "lamden_contract": "token1", "decimals": None},
            "mint":
                {"signer": self.c.signer, "ethereum_contract": ETH_TOKEN4, "amount": "0x14",
                "lamden_wallet": "user"},
            "msg":
                "Impossible amount of decimals shouldn't work"},
        ]

        for i, case in enumerate(test_cases):
            with self.subTest(i=i):
                if "add_token" in case:
                    self.setUp()
                    decimals = case["add_token"]["decimals"]
                    self.router.add_token(**(case["add_token"]))

                supposed_balances = calcBalanceAfterMint(self.c, "token1", case["mint"], decimals)
                nonces_before = getAllHashValues(self.c, ROUTER_NAME, "nonces")

                self.router.mint(**case["mint"])

                balances_after = getAllHashValues(self.c,  "token1", "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(supposed_balances, balances_after)
                self.assertEqual(nonces_before, nonces_after)

        for i, case in enumerate(fail_cases):
            with self.subTest(i=i):
                if "add_token" in case:
                    self.setUp()
                    decimals = case["add_token"]["decimals"]
                    self.router.add_token(**(case["add_token"]))

                balances_before = getAllHashValues(self.c, "token1", "balances")
                nonces_before = getAllHashValues(self.c, ROUTER_NAME, "nonces")

                with self.assertRaises(BaseException, msg=case["msg"]):
                    self.router.mint(**case["mint"])

                balances_after = getAllHashValues(self.c, "token1", "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(nonces_before, nonces_after)
                self.assertEqual(balances_before, balances_after)

    def test_add_token(self):
        ETH_TOKEN = "0x0000000000000000000000000000000000000000"
        test_cases = [
            {"ethereum_contract": ETH_TOKEN, "lamden_contract": "token1", "decimals": 18},
            # Different ethereum_contract but same lamden_contract
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "token1", "decimals": 18},
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "token1", "decimals": 18},
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "token1", "decimals": 0},
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "token1", "decimals": -3},
        ]

        fail_cases = [
            # Bad ethereum_contract
            # {"ethereum_contract": "0000000000000000000000000000000000000000", "lamden_contract": "token1", "decimals": 18},
            # {"ethereum_contract": "", "lamden_contract": "token1", "decimals": 18},
            # {"ethereum_contract": "0x3333", "lamden_contract": "token1", "decimals": 18},
            # {"ethereum_contract": "3333", "lamden_contract": "token1", "decimals": 18},
            
            # Attempt to add already added ethereum_contract
            {"ethereum_contract": ETH_TOKEN, "lamden_contract": "token1", "decimals": 18},

            # Attempt to add tokens that do not enforce the necessarty interface
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "token_no_transfer",
            "decimals": 18},
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "token_no_mint",
            "decimals": 18},
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "token_no_allowance",
            "decimals": 18},
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "token_no_approve",
            "decimals": 18},
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "token_no_transfer_from",
            "decimals": 18},
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "token_wrong_mint",
            "decimals": 18},

            # Not existing lamden_contract
            {"ethereum_contract": randomEthAddress(), "lamden_contract": "not_existing",
            "decimals": 18},

            # Bad decimals
            # {"ethereum_contract": randomEthAddress(), "lamden_contract": "token1", "decimals": ""},
            # {"ethereum_contract": randomEthAddress(), "lamden_contract": "token1", "decimals": None},

            # Non-owner trying to add_token
            {"signer": "user", "ethereum_contract": randomEthAddress(), "lamden_contract": "token1",
            "decimals": 18},
        ]

        for i, case in enumerate(test_cases):
            with self.subTest(i=i):
                lamden_contract = case["lamden_contract"]
                balances_before = getAllHashValues(self.c, lamden_contract, "balances")
                nonces_before = getAllHashValues(self.c, ROUTER_NAME, "nonces")

                self.router.add_token(**case)

                balances_after = getAllHashValues(self.c, lamden_contract, "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(balances_before, balances_after)
                self.assertEqual(nonces_before, nonces_after)

        for case in fail_cases:
            with self.subTest(i=i):
                lamden_contract = case["lamden_contract"]

                if lamden_contract != "token1":
                    try:
                        with open(f"tests/contracts/{lamden_contract}.py") as f:
                            code = f.read()
                            self.c.submit(code, name=lamden_contract)
                    except:
                        pass

                balances_before = getAllHashValues(self.c, lamden_contract, "balances")
                nonces_before = getAllHashValues(self.c, ROUTER_NAME, "nonces")

                with self.assertRaises(BaseException, msg=case):
                    self.router.add_token(**case)

                balances_after = getAllHashValues(self.c, lamden_contract, "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(nonces_before, nonces_after)
                self.assertEqual(balances_before, balances_after)
            
    @unittest.skip("TODO")
    def testFailUnsupportedInterface(self):
        fail_contracts = ['token_no_allowance', 'token_no_approve', 'token_no_mint',
        'token_no_transfer', 'token_no_transfer_from', 'token_wrong_ming',
        "not_existing"]

        args = {"ethereum_contract": self.ETH_TOKEN1, }

        for i, lamden_contract in enumerate(fail_contracts):
            try:
                with open(f"tests/contracts/{lamden_contract}.py") as f:
                    code = f.read()
                    self.c.submit(code, name=lamden_contract)
            except:
                pass

            with self.subTest(i=i):
                with self.assertRaises(BaseException):
                    self.router.burn(ethereum_contract=randomEthAddress(), lamden_contract=lamden_contract,
                    decimals=18)

                # TODO
                approvals_after = getAllHashValues(self.c, "token1", "balances", level=2)
                balances_after = getAllHashValues(self.c, "token1", "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(self.balances, balances_after)
                self.assertEqual(self.nonces, nonces_after)
                self.assertEqual(self.approved, approvals_after)

class TestBurn(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.c = client
        self.c.flush()

        with open("lamden/router.py") as f:
            code = f.read()
            self.c.submit(code, name=ROUTER_NAME)
            self.router = self.c.get_contract(ROUTER_NAME)    

        with open("lamden/token.py") as f:
            self.token_code = f.read()
            self.c.submit(self.token_code, "token1")
            self.token1 = self.c.get_contract("token1")

        self.token1.quick_write(variable="balances", key="user", value=decimal.ContractingDecimal(100))
        self.token1.quick_write(variable="balances", key="user2", value=decimal.ContractingDecimal(100))
        self.token1.approve(signer="user", amount=100, to=ROUTER_NAME)

        self.ETH_TOKEN1 = "0x1111111111111111111111111111111111111111"
        self.router.add_token(ethereum_contract=self.ETH_TOKEN1, lamden_contract="token1",
            decimals=18)

        self.approved = getAllHashValues(self.c, "token1", "balances", level=2)
        self.balances = getAllHashValues(self.c, "token1", "balances")
        self.nonces = getAllHashValues(self.c, ROUTER_NAME, "nonces")
        # self.approved = decimal.ContractingDecimal(100)

    def testBurn(self):
        self.ETH_ADDRESS = "0x2222222222222222222222222222222222222222"
        test_cases=[
            {"burn":
                {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": self.ETH_ADDRESS,
                "lamden_address":"user", "amount": 10},
            "abi":
                "0"*24 + self.ETH_TOKEN1[2:] +
                "0000000000000000000000000000000000000000000000008ac7230489e80000" + 
                "0000000000000000000000000000000000000000000000000000000000000001" + 
                "0"*24 + self.ETH_ADDRESS[2:]},
            {"burn":
                {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": self.ETH_ADDRESS,
                "lamden_address":"user", "amount": 10.005},
            "abi":
                "0"*24 + self.ETH_TOKEN1[2:] +
                "0000000000000000000000000000000000000000000000008ad8e67dc1c88000" + 
                "0000000000000000000000000000000000000000000000000000000000000002" +
                "0"*24 + self.ETH_ADDRESS[2:]},
            {"burn":
                {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": self.ETH_ADDRESS,
                "lamden_address":"user", "amount": decimal.ContractingDecimal("10.000000000000000001")},
            "abi":
                "0"*24 + self.ETH_TOKEN1[2:] +
                "0000000000000000000000000000000000000000000000008ac7230489e80001" + 
                "0000000000000000000000000000000000000000000000000000000000000003" +
                "0"*24 + self.ETH_ADDRESS[2:]},
            {"burn":
                {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": self.ETH_ADDRESS,
                "lamden_address":"user", "amount": decimal.ContractingDecimal("10.0000000000000000001")},
            "abi":
                "0"*24 + self.ETH_TOKEN1[2:] +
                "0000000000000000000000000000000000000000000000008ac7230489e80000" + 
                "0000000000000000000000000000000000000000000000000000000000000004" +
                "0"*24 + self.ETH_ADDRESS[2:]},
        ]

        for i,case in enumerate(test_cases):
            with self.subTest(i=i):
                self.balances = calcBalancesAfterBurn(self.c, "token1", case["burn"])
                self.nonces = incrementNonces(self.nonces, case["burn"]["ethereum_address"])
                self.approved["user", ROUTER_NAME] -= case["burn"]["amount"]

                abi = self.router.burn(**(case["burn"])) 
                self.assertEqual(abi, case["abi"])

                approvals_after = getAllHashValues(self.c, "token1", "balances", level=2)
                balances_after = getAllHashValues(self.c, "token1", "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(self.balances, balances_after)
                self.assertEqual(self.nonces, nonces_after)
                self.assertEqual(self.approved, approvals_after)


    def testFailEthereumContract(self):
        cases = [
            {"ethereum_contract": randomEthAddress(), "ethereum_address": randomEthAddress(),
            "lamden_address": "user", "amount": 10},
            {"ethereum_contract": "0x333", "ethereum_address": randomEthAddress(),
            "lamden_address": "user", "amount": 10},
            {"ethereum_contract": self.ETH_TOKEN1[2:], "ethereum_address": randomEthAddress(),
            "lamden_address": "user", "amount": 10},
            {"ethereum_contract": "", "ethereum_address": randomEthAddress(),
            "lamden_address": "user", "amount": 10},
            {"ethereum_contract": None, "ethereum_address": randomEthAddress(),
            "lamden_address": "user", "amount": 10},
        ]

        for i, case in enumerate(cases):
            with self.subTest(i=i):
                with self.assertRaises(BaseException):
                    self.router.burn(**case)

                approvals_after = getAllHashValues(self.c, "token1", "balances", level=2)
                balances_after = getAllHashValues(self.c, "token1", "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(self.balances, balances_after)
                self.assertEqual(self.nonces, nonces_after)
                self.assertEqual(self.approved, approvals_after)


    def testFailNonOwnerCall(self):
        cases = [
            {"signer": "user", "ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "user", "amount": 10},
            {"signer": "user", "ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": ROUTER_NAME, "amount": 10},
            {"signer": "user", "ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "sys", "amount": 10},
            {"signer": "user", "ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "token", "amount": 10},
            {"signer": "foreigner", "ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": ROUTER_NAME, "amount": 10},
        ]

        for i, case in enumerate(cases):
            with self.subTest(i=i):
                with self.assertRaises(BaseException):
                    self.router.burn(**case)

                approvals_after = getAllHashValues(self.c, "token1", "balances", level=2)
                balances_after = getAllHashValues(self.c, "token1", "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(self.balances, balances_after)
                self.assertEqual(self.nonces, nonces_after)
                self.assertEqual(self.approved, approvals_after)


    @unittest.skip("FAILS")
    def testFailEthereumAddress(self):
        cases = [
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": "1111111111111111111111111111111111111111",
            "lamden_address": "user", "amount": 10},
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": "",
            "lamden_address": "user", "amount": 20},
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": None,
            "lamden_address": "user", "amount": 30},
        ]

        for i, case in enumerate(cases):
            with self.subTest(i=i):
                with self.assertRaises(BaseException):
                    self.router.burn(**case)

                approvals_after = getAllHashValues(self.c, "token1", "balances", level=2)
                balances_after = getAllHashValues(self.c, "token1", "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(self.balances, balances_after)
                self.assertEqual(self.nonces, nonces_after)
                self.assertEqual(self.approved, approvals_after)


    def testFailLamdenAddress(self):
        cases = [
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": None, "amount": 10},
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "", "amount": 10},
            # User2 has not approved ROUTER
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "user2", "amount": 10},
            # user3 has 0 tokens
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "user3", "amount": 10},
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "user3", "amount": 10},
        ]

        for i, case in enumerate(cases):
            with self.subTest(i=i):
                with self.assertRaises(BaseException):
                    self.router.burn(**case)

                approvals_after = getAllHashValues(self.c, "token1", "balances", level=2)
                balances_after = getAllHashValues(self.c, "token1", "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(self.balances, balances_after)
                self.assertEqual(self.nonces, nonces_after)
                self.assertEqual(self.approved, approvals_after)


    def testFailAmount(self):
        cases = [
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": None, "amount": ""},
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "", "amount": None},
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "user2", "amount": -10},
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "user3", "amount": 0x1440},
            {"ethereum_contract": self.ETH_TOKEN1, "ethereum_address": randomEthAddress(),
            "lamden_address": "user3", "amount": "0x1440"},
        ]

        for i, case in enumerate(cases):
            with self.subTest(i=i):
                with self.assertRaises(BaseException):
                    self.router.burn(**case)

                approvals_after = getAllHashValues(self.c, "token1", "balances", level=2)
                balances_after = getAllHashValues(self.c, "token1", "balances")
                nonces_after = getAllHashValues(self.c, ROUTER_NAME, "nonces")
                self.assertEqual(self.balances, balances_after)
                self.assertEqual(self.nonces, nonces_after)
                self.assertEqual(self.approved, approvals_after)

        
if __name__ == '__main__':
    unittest.main()
