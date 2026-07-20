"""Doubly linked list used by the hash map and the LRU tracker."""


class Node:
    """A node containing links to both adjacent nodes and one data value."""

    def __init__(self, data):
        self.prev = None
        self.next = None
        self.data = data


class DoublyLinkedList:
    """A sentinel-based doubly linked list with O(1) mutations."""

    def __init__(self):
        self.head = Node(None)
        self.tail = Node(None)
        self.head.next = self.tail
        self.tail.prev = self.head
        self._size = 0

    def size(self):
        """Return the number of data nodes in the list."""
        return self._size

    def is_empty(self):
        return self._size == 0

    def insert_front(self, data):
        """Insert data at the front and return the newly created node."""
        node = Node(data)
        self._insert_between(node, self.head, self.head.next)
        return node

    def insert_back(self, data):
        """Insert data at the back and return the newly created node."""
        node = Node(data)
        self._insert_between(node, self.tail.prev, self.tail)
        return node

    def remove_front(self):
        """Remove and return the first data value, or None if empty."""
        if self.is_empty():
            return None
        return self.remove_node(self.head.next)

    def remove_back(self):
        """Remove and return the last data value, or None if empty."""
        if self.is_empty():
            return None
        return self.remove_node(self.tail.prev)

    def remove_node(self, node):
        """Remove a known node in O(1) and return its data."""
        if node is None or node is self.head or node is self.tail:
            raise ValueError("cannot remove a sentinel or missing node")
        if node.prev is None or node.next is None:
            raise ValueError("node is not linked to this list")

        node.prev.next = node.next
        node.next.prev = node.prev
        self._size -= 1

        data = node.data
        node.prev = None
        node.next = None
        return data

    def move_to_front(self, node):
        """Move a known node to the front without creating a new node."""
        if node is None or node is self.head or node is self.tail:
            raise ValueError("cannot move a sentinel or missing node")
        if node.prev is None or node.next is None:
            raise ValueError("node is not linked to this list")
        if node.prev is self.head:
            return

        node.prev.next = node.next
        node.next.prev = node.prev

        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _insert_between(self, node, previous, following):
        node.prev = previous
        node.next = following
        previous.next = node
        following.prev = node
        self._size += 1

