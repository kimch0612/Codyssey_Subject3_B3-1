"""Core Mini Redis policies built from the custom data structures."""

import time

from doubly_linked_list import DoublyLinkedList
from hash_map import HashMap
from min_heap import HeapEntry, MinHeap


class OutOfMemoryError(Exception):
    """Raised when one entry cannot fit within maxmemory."""


class RedisEntry:
    """Value metadata stored as the value of the main hash map."""

    def __init__(self, value, lru_node, expire_at=None):
        self.value = value
        self.lru_node = lru_node
        self.expire_at = expire_at


class MiniRedis:
    """In-memory string store with LRU eviction and heap-based TTL."""

    def __init__(self, clock=None):
        self.data = HashMap()
        self.lru = DoublyLinkedList()
        self.expiry_heap = MinHeap()

        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0
        self._clock = clock if clock is not None else time.monotonic

    def set(self, key, value):
        """Store a string value, reset its TTL, and update LRU order."""
        self._require_string(key, "key")
        self._require_string(value, "value")
        self._purge_expired()

        new_size = self._entry_size(key, value)
        if self.maxmemory > 0 and new_size > self.maxmemory:
            # Reject before mutation so an oversized overwrite is atomic.
            raise OutOfMemoryError()

        entry = self.data.get(key)
        if entry is None:
            lru_node = self.lru.insert_front(key)
            entry = RedisEntry(value, lru_node)
            self.data.put(key, entry)
            self.used_memory += new_size
        else:
            old_size = self._entry_size(key, entry.value)
            self.used_memory += new_size - old_size
            entry.value = value
            entry.expire_at = None
            self.lru.move_to_front(entry.lru_node)

        self._evict_until_within_limit()

    def get(self, key):
        """Return a value and mark it recently used, or None if absent."""
        self._require_string(key, "key")
        self._purge_expired()
        entry = self.data.get(key)
        if entry is None:
            return None

        self.lru.move_to_front(entry.lru_node)
        return entry.value

    def delete(self, key):
        """Delete a key from data, LRU, and logical TTL state."""
        self._require_string(key, "key")
        self._purge_expired()
        entry = self.data.get(key)
        if entry is None:
            return False

        self._delete_existing(key, entry)
        return True

    def exists(self, key):
        self._require_string(key, "key")
        self._purge_expired()
        return self.data.contains(key)

    def dbsize(self):
        self._purge_expired()
        return self.data.size()

    def keys(self):
        self._purge_expired()
        return self.data.keys()

    def config_set_maxmemory(self, byte_limit):
        """Set the byte limit; zero means unlimited."""
        self._purge_expired()
        if not isinstance(byte_limit, int) or byte_limit < 0:
            raise ValueError("maxmemory must be a non-negative integer")
        self.maxmemory = byte_limit

    def info_memory(self):
        """Return used_memory, maxmemory, and evicted_keys as a tuple."""
        self._purge_expired()
        return self.used_memory, self.maxmemory, self.evicted_keys

    def expire(self, key, seconds):
        """Set a key's expiration in seconds and return whether it existed."""
        self._require_string(key, "key")
        now = self._clock()
        self._purge_expired(now)
        entry = self.data.get(key)
        if entry is None:
            return False

        if seconds <= 0:
            self._delete_existing(key, entry)
            return True

        expire_at = now + seconds
        entry.expire_at = expire_at
        self.expiry_heap.push(HeapEntry(expire_at, key))
        return True

    def ttl(self, key):
        """Return -2 for missing, -1 for persistent, or remaining seconds."""
        self._require_string(key, "key")
        now = self._clock()
        self._purge_expired(now)
        entry = self.data.get(key)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1

        remaining = entry.expire_at - now
        if remaining <= 0:
            self._delete_existing(key, entry)
            return -2
        return int(remaining)

    def _purge_expired(self, now=None):
        """Remove all currently expired entries from the heap's minimum."""
        if now is None:
            now = self._clock()

        while True:
            heap_entry = self.expiry_heap.peek()
            if heap_entry is None or heap_entry.expire_at > now:
                return

            self.expiry_heap.pop()
            entry = self.data.get(heap_entry.key)

            # DEL, SET, eviction, or a newer EXPIRE can make a heap record stale.
            if entry is None or entry.expire_at != heap_entry.expire_at:
                continue
            self._delete_existing(heap_entry.key, entry)

    def _evict_until_within_limit(self):
        while (
            self.maxmemory > 0
            and self.used_memory > self.maxmemory
            and not self.lru.is_empty()
        ):
            key = self.lru.remove_back()
            entry = self.data.get(key)
            if entry is None:
                raise RuntimeError("LRU and data hash map are inconsistent")
            self._delete_existing(
                key,
                entry,
                is_eviction=True,
                lru_already_removed=True,
            )

    def _delete_existing(
        self,
        key,
        entry,
        is_eviction=False,
        lru_already_removed=False,
    ):
        """Centralize all state changes for every kind of deletion."""
        self.data.remove(key)
        if not lru_already_removed:
            self.lru.remove_node(entry.lru_node)

        self.used_memory -= self._entry_size(key, entry.value)
        entry.expire_at = None
        entry.lru_node = None

        if is_eviction:
            self.evicted_keys += 1

    @staticmethod
    def _entry_size(key, value):
        return len(key.encode("utf-8")) + len(value.encode("utf-8"))

    @staticmethod
    def _require_string(value, label):
        if not isinstance(value, str):
            raise TypeError("{} must be a string".format(label))

