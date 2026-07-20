"""A string-keyed hash map implemented with separate chaining."""

from doubly_linked_list import DoublyLinkedList


class HashEntry:
    """One key-value entry stored in a bucket chain."""

    def __init__(self, key, value):
        self.key = key
        self.value = value


class HashMap:
    """Hash map using a custom hash function and linked-list chaining."""

    MAX_LOAD_FACTOR = 0.75

    def __init__(self, initial_capacity=8):
        if initial_capacity <= 0:
            raise ValueError("initial capacity must be positive")

        self.capacity = initial_capacity
        self.buckets = self._new_bucket_array(self.capacity)
        self._size = 0

    def put(self, key, value):
        """Insert or update a key and return True only for a new key."""
        self._require_string_key(key)
        bucket = self.buckets[self._bucket_index(key)]
        node = bucket.head.next

        while node is not bucket.tail:
            entry = node.data
            if entry.key == key:
                entry.value = value
                return False
            node = node.next

        bucket.insert_back(HashEntry(key, value))
        self._size += 1

        if self._size / self.capacity > self.MAX_LOAD_FACTOR:
            self._resize(self.capacity * 2)
        return True

    def get(self, key):
        """Return the value for key, or None when the key is absent."""
        self._require_string_key(key)
        entry = self._find_entry(key)
        if entry is None:
            return None
        return entry.value

    def remove(self, key):
        """Remove key and return its value, or None when absent."""
        self._require_string_key(key)
        bucket = self.buckets[self._bucket_index(key)]
        node = bucket.head.next

        while node is not bucket.tail:
            entry = node.data
            if entry.key == key:
                value = entry.value
                bucket.remove_node(node)
                self._size -= 1
                return value
            node = node.next
        return None

    def contains(self, key):
        self._require_string_key(key)
        return self._find_entry(key) is not None

    def keys(self):
        """Return every key. Ordering is intentionally unspecified."""
        result = []
        for bucket in self.buckets:
            node = bucket.head.next
            while node is not bucket.tail:
                result.append(node.data.key)
                node = node.next
        return result

    def size(self):
        return self._size

    def _hash(self, key):
        """Return a stable 32-bit polynomial hash for a UTF-8 string."""
        hash_value = 0
        for byte in key.encode("utf-8"):
            hash_value = (hash_value * 31 + byte) & 0xFFFFFFFF
        return hash_value

    def _bucket_index(self, key):
        return self._hash(key) % self.capacity

    def _find_entry(self, key):
        bucket = self.buckets[self._bucket_index(key)]
        node = bucket.head.next
        while node is not bucket.tail:
            entry = node.data
            if entry.key == key:
                return entry
            node = node.next
        return None

    def _resize(self, new_capacity):
        """Double the bucket table and rehash all existing entries."""
        old_buckets = self.buckets
        self.capacity = new_capacity
        self.buckets = self._new_bucket_array(new_capacity)
        old_size = self._size
        self._size = 0

        for bucket in old_buckets:
            node = bucket.head.next
            while node is not bucket.tail:
                entry = node.data
                self._insert_without_resize(entry.key, entry.value)
                node = node.next

        if self._size != old_size:
            raise RuntimeError("hash map size changed during rehash")

    def _insert_without_resize(self, key, value):
        bucket = self.buckets[self._bucket_index(key)]
        bucket.insert_back(HashEntry(key, value))
        self._size += 1

    @staticmethod
    def _new_bucket_array(capacity):
        return [DoublyLinkedList() for _ in range(capacity)]

    @staticmethod
    def _require_string_key(key):
        if not isinstance(key, str):
            raise TypeError("hash map keys must be strings")

