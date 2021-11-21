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

def calcBalanceAfterMint(token, token_name, case, decimals):
    old_balances = getAllHashValues(token, token_name, "balances")
    amount = int(case["mint"]["amount"], 16) / (10 ** decimals)
    account = case["mint"]["lamden_wallet"]
    if account in old_balances:
        old_balances[account] += amount
    else: 
        old_balances[account] = decimal.ContractingDecimal(amount)
    return old_balances

class TestRouter(unittest.TestCase):
    def setUp(self):
        self.c = client
        self.c.flush()

        with open("lamden/router.py") as f:
            code = f.read()
            self.c.submit(code, name=ROUTER_NAME)
            self.router = self.c.get_contract(ROUTER_NAME)    

        # Save code of a token so that we can create tokens later
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

                supposed_balances = calcBalanceAfterMint(self.c, "token1", case, decimals)
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

if __name__ == '__main__':
    unittest.main()
