import unittest

from doubly_linked_list import DoublyLinkedList


class DoublyLinkedListTest(unittest.TestCase):
    def test_insert_remove_and_move_are_consistent(self):
        linked_list = DoublyLinkedList()
        first = linked_list.insert_back("first")
        second = linked_list.insert_back("second")
        linked_list.insert_front("zero")

        self.assertEqual(linked_list.size(), 3)
        self.assertEqual(linked_list.remove_front(), "zero")

        linked_list.move_to_front(second)
        self.assertEqual(linked_list.remove_front(), "second")
        self.assertEqual(linked_list.remove_node(first), "first")
        self.assertTrue(linked_list.is_empty())

    def test_empty_removals_return_none(self):
        linked_list = DoublyLinkedList()
        self.assertIsNone(linked_list.remove_front())
        self.assertIsNone(linked_list.remove_back())


if __name__ == "__main__":
    unittest.main()

