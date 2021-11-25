#tests/test_static.py
import unittest
from contracting.client import ContractingClient
from tests.util import submit_compiled

# These are tests for the static methods of the lamden_bridge.py and the router.py
# contracts.

client = ContractingClient()

class TestStatic(unittest.TestCase):
    def setUp(self):
        self.c = client
        self.c.flush()


    def testLeftPad(self):
        test_cases = [
            ({"s": ""}, "0"*64),
            ({"s": "0100"}, "0"*60+"0100"),
            ({"s": "0"*100}, "0"*64),
            ({"s": "1"+"0"*100}, "1"+"0"*63),
            ({"s": "0"*64+"33"}, "0"*64)]

        for case in test_cases:
            result = self.contract.run_private_function(f="left_pad", **(case[0]))
            self.assertEqual(len(result), 64, msg="Results of \"left_pad\" should have \
                length 64, but has length {len(result)}")
            self.assertEqual(result, case[1])


    def testUnpackUint256(self):
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

        for case in test_cases:
            result = self.contract.run_private_function(f="unpack_uint256", **(case[0]))
            self.assertEqual(result, case[1])


    def test_unpack_uint256(self):
        fail_cases = [
            {"uint": "str", "decimals": 18},
            {"uint": 1.6, "decimals": 18},
            {"uint": "1.6", "decimals": 18},
            {"uint": "0x32", "decimals": "abc"},
        ]

        for case in fail_cases:
            with self.assertRaises(BaseException):
                self.contract.run_private_function(f="unpack_uint256", **case)


    def testPackAmount(self):
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

        for case in test_cases:
            result = self.contract.run_private_function(f="pack_amount", **(case[0]))
            self.assertEqual(result, case[1])


    def testFailPackAmount(self):
        fail_cases = [
            {"amount": "abc", "decimals": 2},
            {"amount": "abc", "decimals": 18},
            {"amount": 70, "decimals": "abc"},
        ]

        for case in fail_cases:
            with self.assertRaises(BaseException):
                self.contract.run_private_function(f="pack_amount", **case)


    def testPackEthAddress(self):
        test_cases = [
            ({"address": "0x0000000000000000000000000000000000000000"},
                "0000000000000000000000000000000000000000000000000000000000000000"),
            ({"address": "0x54dbb737eac5007103e729e9ab7ce64a6850a310"},
                "00000000000000000000000054dbb737eac5007103e729e9ab7ce64a6850a310"),
            ({"address": "0x54DBB737EAC5007103E729E9AB7CE64A6850A310"},
                "00000000000000000000000054DBB737EAC5007103E729E9AB7CE64A6850A310"),
        ]
        for case in test_cases:
            result = self.contract.run_private_function(f="pack_eth_address", **(case[0]))
            self.assertEqual(result, case[1])


    def testFailPackEthAddress(self):
        fail_prefix_cases = [
            {"address": ""},
            {"address": "0X54dbb737eac5007103e729e9ab7ce64a6850a310"},
            {"address": "54dbb737eac5007103e729e9ab7ce64a6850a310"},
            {"address": "0o54dbb737eac5007103e729e9ab7ce64a6850a310"},
            {"address": "0x"},
            {"address": "0x54dbb"},
            {"address": "0x54dbb737eac5007103e729e9ab7ce64a6850a310000000000000"},
            {"address": "0xggdbb737eac5007103e729e9ab7ce64a6850a310"},
            {"address": "0xggdbb737eac5007103e729e9ab7ce64a6850a31#"},
        ]

        for case in fail_prefix_cases:
            with self.assertRaises(BaseException):
                self.contract.run_private_function(f="pack_eth_address", **case)


    def testPackInt(self):
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

        for case in test_cases:
            result = self.contract.run_private_function(f="pack_int", **(case[0]))
            self.assertEqual(result, case[1])


    def testFailPackInt(self):
        fail_int_cases = [
            {"i": "abc"},
            {"i": "0x33"},
            {"i": "1.7"},
            ]

        for case in fail_int_cases:
            with self.assertRaises(ValueError):
                self.contract.run_private_function(f="pack_int", **case)

class TestStaticLamdenBridge(TestStatic):
    def setUp(self):
        super().setUp()

        with open("tests/contracts/currency.py") as f:
            compiled_code = f.read()
        submit_compiled(self.c, "currency", compiled_code, args={"vk": "OwnerOfCurrency"})

        with open("lamden/lamden_bridge.py") as f:
            code = f.read()
            self.c.submit(code, name="lamden_bridge")
            self.contract = self.c.get_contract("lamden_bridge")    

class TestStaticRouter(TestStatic):
    def setUp(self):
        super().setUp()

        with open("lamden/router.py") as f:
            code = f.read()
            self.c.submit(code, name="router")
            self.contract = self.c.get_contract("router")    

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()

    test_cases = [TestStaticLamdenBridge, TestStaticRouter]
    
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
