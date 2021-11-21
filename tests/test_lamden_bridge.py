#tests/test_lamden_bridge.py
import unittest

from contracting.client import ContractingClient
from tests.util import submit_compiled

client = ContractingClient()

ETH_TOKEN = "0xF08eF1668524a98893D97F16Ad134dA8cccefb03"
ETH_ADDRESS = "0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8"


class TestLamdenBridge(unittest.TestCase):
    def setUp(self):
        self.c = client
        self.c.flush()

        with open("tests/contracts/currency.py") as f:
            compiled_code = f.read()

        submit_compiled(self.c, "currency", compiled_code, args={"vk": "OwnerOfCurrency"})
        self.currency = self.c.get_contract("currency")

        with open("lamden/lamden_bridge.py") as f:
            code = f.read()
            args = {"contract_address": ETH_TOKEN,
                "decimals":18}
            self.c.submit(code, name="lamden_bridge", constructor_args=args)
            self.l_bridge = self.c.get_contract("lamden_bridge")    

    def tearDown(self):
        self.c.flush()

    def test_left_pad(self):

        # if not HEX_BYTES == 64:
            # raise unittest.SkipTest("Tests were only written for when HEX_BYTES=64")

        test_cases = [
            ({"s": ""}, "0"*64),
            ({"s": "0100"}, "0"*60+"0100"),
            ({"s": "0"*100}, "0"*64),
            ({"s": "1"+"0"*100}, "1"+"0"*63),
            ({"s": "0"*64+"33"}, "0"*64)]

        for case in test_cases:
            result = self.l_bridge.run_private_function(f="left_pad", **(case[0]))
            self.assertEqual(len(result), 64, msg="Results of \"left_pad\" should have \
                length 64, but has length {len(result)}")
            self.assertEqual(result, case[1])

    def test_unpack_uint256(self):
        test_cases = [
            ({"uint": "0x32", "decimals": 18}, 5e-17),
            ({"uint": "32", "decimals": 18}, 5e-17),
            ({"uint": "0x10000", "decimals": 18}, 6.5536e-14),
            ({"uint": "10000", "decimals": 18}, 6.5536e-14),
            ({"uint": "0x10000", "decimals": 1}, 6553.6),
            ({"uint": "10000", "decimals": 1}, 6553.6),
            ({"uint": "0x1"+"0"*18, "decimals": 18}, 4722.366482869646),
            ({"uint": "1"+"0"*18, "decimals": 18}, 4722.366482869646),
            ({"uint": "0x1"+"0", "decimals": 1}, 1.6),
            ({"uint": "1"+"0", "decimals": 1}, 1.6),
            ({"uint": "0x0", "decimals": 1}, 0),
            ({"uint": "0", "decimals": 1}, 0),
        ]

        fail_cases = [
            {"uint": "str", "decimals": 18},
            {"uint": 1.6, "decimals": 18},
            {"uint": "1.6", "decimals": 18},
            {"uint": "0x32", "decimals": "abc"},
        ]

        for case in test_cases:
            result = self.l_bridge.run_private_function(f="unpack_uint256", **(case[0]))
            self.assertEqual(result, case[1])

        for case in fail_cases:
            with self.assertRaises(BaseException):
                self.l_bridge.run_private_function(f="unpack_uint256", **case)

    def test_pack_amount(self):
        test_cases = [
            ({"amount": 1.5, "decimals": 18},
                "00000000000000000000000000000000000000000000000014d1120d7b160000"),
            ({"amount": 0, "decimals": 18},
                "0000000000000000000000000000000000000000000000000000000000000000"),
            ({"amount": 1.555, "decimals": 0},
                "0000000000000000000000000000000000000000000000000000000000000001"),
            ({"amount": 1.555, "decimals": 1},
                "000000000000000000000000000000000000000000000000000000000000000f"),
            ({"amount": 1.555, "decimals": 2},
                "000000000000000000000000000000000000000000000000000000000000009b"),
            ({"amount": 1.555, "decimals": 3},
                "0000000000000000000000000000000000000000000000000000000000000613"),
            ({"amount": 1.555, "decimals": 4},
                "0000000000000000000000000000000000000000000000000000000000003cbe"),
            ({"amount": 1.6e-17, "decimals": 18},
                "0000000000000000000000000000000000000000000000000000000000000010"),
            ({"amount": 2.56e-16, "decimals": 18},
                "0000000000000000000000000000000000000000000000000000000000000100"),
            ({"amount": 1e61, "decimals": 18},
                "0000000000000000000000000000000000000001431e0fae6d7217caa0000000"),
        ]

        fail_cases = [
            {"amount": "abc", "decimals": 2},
            {"amount": "abc", "decimals": 18},
            {"amount": 70, "decimals": "abc"},
        ]

        for case in test_cases:
            result = self.l_bridge.run_private_function(f="pack_amount", **(case[0]))
            self.assertEqual(result, case[1])

        for case in fail_cases:
            with self.assertRaises(BaseException):
                self.l_bridge.run_private_function(f="pack_amount", **case)

    def test_pack_eth_address(self):
        test_cases = [
            ({"address": "0x0000000000000000000000000000000000000000"},
                "0000000000000000000000000000000000000000000000000000000000000000"),
            ({"address": "0x54dbb737eac5007103e729e9ab7ce64a6850a310"},
                "00000000000000000000000054dbb737eac5007103e729e9ab7ce64a6850a310"),
            ({"address": "0x54DBB737EAC5007103E729E9AB7CE64A6850A310"},
                "00000000000000000000000054DBB737EAC5007103E729E9AB7CE64A6850A310"),
        ]

        fail_prefix_cases = [
            {"address": ""},
            {"address": "0X54dbb737eac5007103e729e9ab7ce64a6850a310"},
            {"address": "54dbb737eac5007103e729e9ab7ce64a6850a310"},
            {"address": "0o54dbb737eac5007103e729e9ab7ce64a6850a310"},
        ]

        fail_len_cases = [
            {"address": "0x"},
            {"address": "0x54dbb"},
            {"address": "0x54dbb737eac5007103e729e9ab7ce64a6850a310000000000000"},
        ]

        fail_hex_cases = [
            {"address": "0xggdbb737eac5007103e729e9ab7ce64a6850a310"},
            {"address": "0xggdbb737eac5007103e729e9ab7ce64a6850a31#"},
        ]

        for case in test_cases:
            result = self.l_bridge.run_private_function(f="pack_eth_address", **(case[0]))
            self.assertEqual(result, case[1])

        for case in fail_prefix_cases:
            with self.assertRaises(AssertionError):
                self.l_bridge.run_private_function(f="pack_eth_address", **case)

        for case in fail_len_cases:
            with self.assertRaises(AssertionError):
                self.l_bridge.run_private_function(f="pack_eth_address", **case)

        for case in fail_hex_cases:
            with self.assertRaises(ValueError):
                self.l_bridge.run_private_function(f="pack_eth_address", **case)

    def test_pack_int(self):
        test_cases = [
            ({"i": "0"},
                "0000000000000000000000000000000000000000000000000000000000000000"),
            ({"i": 0},
                "0000000000000000000000000000000000000000000000000000000000000000"),
            ({"i": "256"},
                "0000000000000000000000000000000000000000000000000000000000000100"),
            ({"i": 115792089237316195423570985008687907853269984665640564039457584007913129639936},
                "1000000000000000000000000000000000000000000000000000000000000000"),
            ({"i": "115792089237316195423570985008687907853269984665640564039457584007913129639936"},
                "1000000000000000000000000000000000000000000000000000000000000000"),
            ({"i": 1.7},
                "0000000000000000000000000000000000000000000000000000000000000001"),
            ({"i": 0x10},
                "0000000000000000000000000000000000000000000000000000000000000010"),
        ]

        fail_int_cases = [
            {"i": "abc"},
            {"i": "0x33"},
            {"i": "1.7"},
            ]

        for case in test_cases:
            result = self.l_bridge.run_private_function(f="pack_int", **(case[0]))
            self.assertEqual(result, case[1])

        for case in fail_int_cases:
            with self.assertRaises(ValueError):
                self.l_bridge.run_private_function(f="pack_int", **case)

    def getBalances(self, *args):
        balances = {}
        for a in args:
            balances[a] = self.currency.balance_of(account=a)
        return balances

    def getNonce(self):
        nonce = self.l_bridge.quick_read(variable="nonces", key=ETH_ADDRESS)
        if not nonce:
            nonce = 0
        return nonce

    def test_deposit(self):
        # Inrease the balance of "user", so that "user" has some tau to deposit
        self.c.set_var(contract="currency",
                       variable="balances",
                       arguments=["user"],
                       value=100)
        self.c.set_var(contract="currency",
                       variable="balances",
                       arguments=["user2"],
                       value=100)

        # Only "user" has approved lamden_bridge
        self.currency.approve(signer="user", amount=100, to="lamden_bridge")

        test_cases = [
            ({"amount": 1, "ethereum_address": ETH_ADDRESS}, 
                # "000000000000000000000000F08eF1668524a98893D97F16Ad134dA8cccefb030000000000000000000000000000000000000000000000000de0b6b3a76400000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000EA674fdDe714fd979de3EdF0F56AA9716B898ec8"),
                "2467d967d604f32992a2ac4e1ae03b9a86a2ac5069d22e0743e45ee89147319f"),
            ({"amount": 10, "ethereum_address": ETH_ADDRESS}, 
                # "000000000000000000000000F08eF1668524a98893D97F16Ad134dA8cccefb030000000000000000000000000000000000000000000000008ac7230489e800000000000000000000000000000000000000000000000000000000000000000002000000000000000000000000EA674fdDe714fd979de3EdF0F56AA9716B898ec8"),
                "5d3ae41b5df3d3932bf63f401477a244116155ee44308a80228ccb947803fb69"),
            ({"amount": 0.5, "ethereum_address": ETH_ADDRESS}, 
                # "000000000000000000000000F08eF1668524a98893D97F16Ad134dA8cccefb0300000000000000000000000000000000000000000000000006f05b59d3b200000000000000000000000000000000000000000000000000000000000000000003000000000000000000000000EA674fdDe714fd979de3EdF0F56AA9716B898ec8"),
                "f8fd422a9fb49671816e41452583dd90c8a2dd53ee251f64942e770cdaf684d2"),
            ({"amount": 0.5, "ethereum_address": ETH_ADDRESS}, 
                # "000000000000000000000000F08eF1668524a98893D97F16Ad134dA8cccefb0300000000000000000000000000000000000000000000000006f05b59d3b200000000000000000000000000000000000000000000000000000000000000000004000000000000000000000000EA674fdDe714fd979de3EdF0F56AA9716B898ec8"),
                "80960e2f94e9a066c101e948494f081ed33d93e899a7fb608925c4f49357bfb5"),
        ]

        fail_cases = [
            # impossible ethereum_address
            {"signer": "user", "amount": 10, "ethereum_address": ""},
            {"signer": "user", "amount": 10, "ethereum_address": "0X54dbb737eac5007103e729e9ab7ce64a6850a310"},
            {"signer": "user", "amount": 10, "ethereum_address": "54dbb737eac5007103e729e9ab7ce64a6850a310"},
            {"signer": "user", "amount": 10, "ethereum_address": "0o54dbb737eac5007103e729e9ab7ce64a6850a310"},
            {"signer": "user", "amount": 10, "ethereum_address": "0x"},
            {"signer": "user", "amount": 10, "ethereum_address": "0x54dbb"},
            {"signer": "user", "amount": 10, "ethereum_address": "0x54dbb737eac5007103e729e9ab7ce64a6850a310000000000000"},
            {"signer": "user", "amount": 10, "ethereum_address": "0xggdbb737eac5007103e729e9ab7ce64a6850a31"},
            # impossible amount
            {"signer": "user", "amount": 0.0, "ethereum_address": ETH_ADDRESS}, 
            {"signer": "user", "amount": None, "ethereum_address": ETH_ADDRESS}, 
            {"signer": "user", "amount": -10, "ethereum_address": ETH_ADDRESS}, 
            {"signer": "user", "amount": "text", "ethereum_address": ETH_ADDRESS},
            {"signer": "user", "amount": 0x3, "ethereum_address": ETH_ADDRESS}, 
            # user tries to deposit more tau than he has
            {"signer": "user", "amount": 1000, "ethereum_address": ETH_ADDRESS}, 
            # lamden_bridge is not approved to transfer from user2
            {"signer": "user2", "amount": 1000, "ethereum_address": ETH_ADDRESS}, 
            # user3 has 0 tau
            {"signer": "user3", "amount": 1000, "ethereum_address": ETH_ADDRESS}, 
        ]

        relevant_actors = ["user", "lamden_bridge", self.c.signer]

        for case in test_cases:
            balances = self.getBalances(*relevant_actors)
            nonce = self.getNonce()

            result = self.l_bridge.deposit(signer="user", **(case[0]))
            self.assertEqual(result, case[1])
            
            supposed_Balances = dict(balances)
            supposed_Balances["user"] -= case[0]["amount"]
            supposed_Balances["lamden_bridge"] += case[0]["amount"]
            self.assertEqual(self.getBalances(*relevant_actors), supposed_Balances)

            supposed_Nonce = nonce + 1
            current_Nonce = self.getNonce()
            self.assertEqual(current_Nonce, supposed_Nonce)

        for case in fail_cases:
            with self.assertRaises(BaseException):
                result = self.l_bridge.deposit(signer="user", **case)

    def test_withdraw(self):
        # Inrease balance of "lamden_bridge" to pretend as if something is deposited
        self.c.set_var(contract="currency",
                       variable="balances",
                       arguments=["lamden_bridge"],
                       value=100)
        # "user" has some tau
        self.c.set_var(contract="currency",
                       variable="balances",
                       arguments=["user"],
                       value=100)

        # "user" has approved lamden_bridge
        self.currency.approve(signer="user", amount=100, to="lamden_bridge")

        test_cases = [
            {"signer": self.c.signer, "amount": 1, "to": self.c.signer},
            {"signer": self.c.signer, "amount": 10.0, "to": self.c.signer},
            {"signer": self.c.signer, "amount": 10.5, "to": self.c.signer},
            # Owner should also be allowed to send withdrawn tau to accounts other than himself
            {"signer": self.c.signer, "amount": 10.5, "to": "foreigner"},
        ]

        fail_cases = [
            # impossible amount
            {"signer": self.c.signer, "amount": float("inf"), "to": self.c.signer},
            {"signer": self.c.signer, "amount": -10, "to": self.c.signer},
            {"signer": self.c.signer, "amount": 0.0, "to": self.c.signer},
            {"signer": self.c.signer, "amount": None, "to": self.c.signer},
            {"signer": self.c.signer, "amount": "text", "to": self.c.signer},
            # impossible receipient
            {"signer": self.c.signer, "amount": 0.0, "to": 0x10},
            {"signer": self.c.signer, "amount": 0.0, "to": None}, 
            # Non-owner tries to withdraw
            {"signer": "foreigner", "amount": 0.0, "to": "user"},
            {"signer": "user", "amount": 0.0, "to": "user"},
            # Trying to withdraw more than available
            {"signer": self.c.signer, "amount": 1000, "to": self.c.signer},
        ]

        relevant_actors = ["foreigner", "user", "lamden_bridge", self.c.signer]

        for case in test_cases:
            supposed_Balances = self.getBalances(*relevant_actors)
            supposed_Nonce = self.getNonce()

            self.l_bridge.withdraw(**case)
            
            supposed_Balances["lamden_bridge"] -= case["amount"]
            supposed_Balances[case["to"]] += case["amount"]
            self.assertEqual(self.getBalances(*relevant_actors), supposed_Balances)

            currentNonce = self.getNonce()
            self.assertEqual(currentNonce, supposed_Nonce)

        for i, case in enumerate(fail_cases):
            with self.assertRaises(BaseException, msg=f"Failure Case {i}"):
                self.l_bridge.withdraw(**case)

    def test_post_proof(self):
        test_cases = [
            {"signer": self.c.signer, "hashed_abi": "abc", "signed_abi": "def"},
            {"signer": self.c.signer, "hashed_abi": "ghi", "signed_abi": "ijk"},
        ]

        fail_cases = [
            # Non-owner tries to post proof
            {"signer": "foreigner", "hashed_abi": "abc", "signed_abi": "def"},
        ]

        # Tests don't fail when owner posts empty proofs or overwrites proofs

        for case in test_cases:
            self.l_bridge.post_proof(**case)
            
            posted_proof = self.l_bridge.quick_read(variable="proofs", key=case["hashed_abi"])
            self.assertEqual(posted_proof, case["signed_abi"])

        for i, case in enumerate(fail_cases):
            with self.assertRaises(BaseException, msg=f"Failure Case {i}"):
                self.l_bridge.post_proof(**case)


if __name__ == '__main__':
    unittest.main()