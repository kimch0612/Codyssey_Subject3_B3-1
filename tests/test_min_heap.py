import unittest

from min_heap import HeapEntry, MinHeap


class MinHeapTest(unittest.TestCase):
    def test_push_peek_and_pop_follow_expiration_order(self):
        heap = MinHeap()
        heap.push(HeapEntry(30, "c"))
        heap.push(HeapEntry(10, "a"))
        heap.push(HeapEntry(20, "b"))

        self.assertEqual(heap.size(), 3)
        self.assertEqual(heap.peek().key, "a")
        self.assertEqual(heap.pop().expire_at, 10)
        self.assertEqual(heap.pop().expire_at, 20)
        self.assertEqual(heap.pop().expire_at, 30)
        self.assertIsNone(heap.pop())

    def test_equal_expiration_uses_key_as_stable_tie_breaker(self):
        heap = MinHeap()
        heap.push(HeapEntry(10, "b"))
        heap.push(HeapEntry(10, "a"))
        self.assertEqual(heap.pop().key, "a")
        self.assertEqual(heap.pop().key, "b")


if __name__ == "__main__":
    unittest.main()

