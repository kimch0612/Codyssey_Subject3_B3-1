import unittest

from hash_map import HashMap


class HashMapTest(unittest.TestCase):
    def test_collision_is_resolved_by_chaining(self):
        hash_map = HashMap(initial_capacity=4)
        colliding_keys = self._find_collision(hash_map)
        first = colliding_keys[0]
        second = colliding_keys[1]

        self.assertEqual(
            hash_map._bucket_index(first),
            hash_map._bucket_index(second),
        )

        hash_map.put(first, "one")
        hash_map.put(second, "two")
        self.assertEqual(hash_map.get(first), "one")
        self.assertEqual(hash_map.get(second), "two")
        self.assertEqual(hash_map.size(), 2)

        self.assertEqual(hash_map.remove(first), "one")
        self.assertIsNone(hash_map.get(first))
        self.assertEqual(hash_map.get(second), "two")

    def test_capacity_doubles_and_entries_are_rehashed(self):
        hash_map = HashMap(initial_capacity=4)
        for index in range(4):
            hash_map.put("key:{}".format(index), index)

        self.assertEqual(hash_map.capacity, 8)
        self.assertEqual(hash_map.size(), 4)
        for index in range(4):
            self.assertEqual(hash_map.get("key:{}".format(index)), index)

    def test_put_updates_without_growing_size(self):
        hash_map = HashMap()
        self.assertTrue(hash_map.put("key", "old"))
        self.assertFalse(hash_map.put("key", "new"))
        self.assertEqual(hash_map.size(), 1)
        self.assertEqual(hash_map.get("key"), "new")
        self.assertEqual(hash_map.keys(), ["key"])

    @staticmethod
    def _find_collision(hash_map):
        groups = [[] for _ in range(hash_map.capacity)]
        for number in range(100):
            key = "candidate:{}".format(number)
            group = groups[hash_map._bucket_index(key)]
            group.append(key)
            if len(group) == 2:
                return group
        raise AssertionError("failed to find colliding keys")


if __name__ == "__main__":
    unittest.main()

