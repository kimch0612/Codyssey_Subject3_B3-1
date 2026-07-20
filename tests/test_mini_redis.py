import unittest

from mini_redis import MiniRedis, OutOfMemoryError


class FakeClock:
    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class MiniRedisTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock(100.0)
        self.redis = MiniRedis(clock=self.clock)

    def test_basic_string_commands(self):
        self.redis.set("name", "Alice")
        self.assertEqual(self.redis.get("name"), "Alice")
        self.assertTrue(self.redis.exists("name"))
        self.assertEqual(self.redis.dbsize(), 1)
        self.assertEqual(self.redis.keys(), ["name"])
        self.assertTrue(self.redis.delete("name"))
        self.assertFalse(self.redis.delete("name"))
        self.assertFalse(self.redis.exists("name"))

    def test_successful_get_changes_lru_eviction_order(self):
        self.redis.config_set_maxmemory(4)
        self.redis.set("a", "1")
        self.redis.set("b", "2")

        self.assertEqual(self.redis.get("a"), "1")
        self.redis.set("c", "3")

        self.assertIsNone(self.redis.get("b"))
        self.assertEqual(self.redis.get("a"), "1")
        self.assertEqual(self.redis.get("c"), "3")
        self.assertEqual(self.redis.info_memory(), (4, 4, 1))

    def test_utf8_memory_size_and_overwrite_delta(self):
        self.redis.set("한", "가")
        self.assertEqual(self.redis.used_memory, 6)

        self.redis.set("한", "ab")
        self.assertEqual(self.redis.used_memory, 5)

    def test_oversized_entry_is_rejected_atomically(self):
        self.redis.config_set_maxmemory(3)
        self.redis.set("a", "1")
        self.redis.expire("a", 10)

        with self.assertRaises(OutOfMemoryError):
            self.redis.set("a", "long")

        self.assertEqual(self.redis.get("a"), "1")
        self.assertEqual(self.redis.ttl("a"), 10)
        self.assertEqual(self.redis.evicted_keys, 0)

    def test_ttl_codes_and_expiration_cleanup(self):
        self.assertEqual(self.redis.ttl("missing"), -2)
        self.redis.set("temporary", "value")
        self.assertEqual(self.redis.ttl("temporary"), -1)
        self.assertTrue(self.redis.expire("temporary", 5))
        self.assertEqual(self.redis.ttl("temporary"), 5)

        self.clock.advance(4)
        self.assertEqual(self.redis.ttl("temporary"), 1)
        self.clock.advance(1)

        self.assertIsNone(self.redis.get("temporary"))
        self.assertEqual(self.redis.ttl("temporary"), -2)
        self.assertEqual(self.redis.used_memory, 0)
        self.assertEqual(self.redis.evicted_keys, 0)

    def test_non_positive_expire_deletes_immediately(self):
        self.redis.set("key", "value")
        self.assertTrue(self.redis.expire("key", 0))
        self.assertFalse(self.redis.exists("key"))
        self.assertFalse(self.redis.expire("missing", 10))

    def test_set_overwrite_clears_ttl_and_stale_heap_record(self):
        self.redis.set("key", "old")
        self.redis.expire("key", 5)
        self.redis.set("key", "new")
        self.assertEqual(self.redis.ttl("key"), -1)

        self.clock.advance(5)
        self.assertEqual(self.redis.get("key"), "new")

    def test_new_expire_supersedes_old_heap_record(self):
        self.redis.set("key", "value")
        self.redis.expire("key", 5)
        self.redis.expire("key", 10)

        self.clock.advance(5)
        self.assertTrue(self.redis.exists("key"))
        self.clock.advance(5)
        self.assertFalse(self.redis.exists("key"))

    def test_global_purge_keeps_dbsize_keys_and_info_current(self):
        self.redis.set("short", "x")
        self.redis.set("long", "y")
        self.redis.expire("short", 1)
        self.clock.advance(1)

        self.assertEqual(self.redis.dbsize(), 1)
        self.assertEqual(self.redis.keys(), ["long"])
        expected = len("long".encode("utf-8")) + len("y".encode("utf-8"))
        self.assertEqual(self.redis.info_memory()[0], expected)


if __name__ == "__main__":
    unittest.main()

