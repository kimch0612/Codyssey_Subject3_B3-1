import unittest

from command_processor import CommandProcessor
from mini_redis import MiniRedis
from tests.test_mini_redis import FakeClock


class CommandProcessorTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock(10.0)
        self.redis = MiniRedis(clock=self.clock)
        self.processor = CommandProcessor(self.redis)

    def test_basic_commands_and_quoted_value(self):
        self.assertEqual(self.processor.execute('SET user "Alice Kim"'), "OK")
        self.assertEqual(self.processor.execute("GET user"), '"Alice Kim"')
        self.assertEqual(self.processor.execute("EXISTS user"), "(integer) 1")
        self.assertEqual(self.processor.execute("DBSIZE"), "(integer) 1")
        self.assertEqual(self.processor.execute("DEL user"), "(integer) 1")
        self.assertEqual(self.processor.execute("GET user"), "(nil)")

    def test_memory_ttl_and_keys_output(self):
        self.assertEqual(
            self.processor.execute("CONFIG SET maxmemory 20"),
            "OK",
        )
        self.processor.execute("SET a 1")
        self.assertEqual(self.processor.execute("KEYS"), '"a"')
        self.assertEqual(self.processor.execute("EXPIRE a 3"), "(integer) 1")
        self.assertEqual(self.processor.execute("TTL a"), "(integer) 3")
        self.assertEqual(
            self.processor.execute("INFO memory"),
            "used_memory:2\nmaxmemory:20\nevicted_keys:0",
        )

    def test_standard_errors(self):
        self.assertEqual(
            self.processor.execute("HELLO"),
            "(error) ERR unknown command 'HELLO'",
        )
        self.assertEqual(
            self.processor.execute("GET"),
            "(error) ERR wrong number of arguments for 'GET' command",
        )
        self.assertEqual(
            self.processor.execute("CONFIG SET maxmemory abc"),
            "(error) ERR value is not an integer or out of range",
        )
        self.assertEqual(
            self.processor.execute('SET key "unterminated'),
            "(error) ERR syntax error",
        )

    def test_oom_output(self):
        self.processor.execute("CONFIG SET maxmemory 2")
        self.assertEqual(
            self.processor.execute("SET key value"),
            "(error) OOM command not allowed when used_memory > 'maxmemory'",
        )
        self.assertEqual(self.processor.execute("DBSIZE"), "(integer) 0")


if __name__ == "__main__":
    unittest.main()

