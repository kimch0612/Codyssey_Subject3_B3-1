"""A minimum binary heap used to track the nearest TTL expiration."""


class HeapEntry:
    """A TTL record ordered by its absolute expiration time."""

    def __init__(self, expire_at, key):
        self.expire_at = expire_at
        self.key = key


class MinHeap:
    """Array-backed minimum heap implemented without heapq."""

    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)
        self._heapify_up(len(self.items) - 1)

    def pop(self):
        """Remove and return the minimum item, or None when empty."""
        if not self.items:
            return None

        minimum = self.items[0]
        last = self.items.pop()
        if self.items:
            self.items[0] = last
            self._heapify_down(0)
        return minimum

    def peek(self):
        if not self.items:
            return None
        return self.items[0]

    def size(self):
        return len(self.items)

    def _heapify_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if not self._is_less(self.items[index], self.items[parent]):
                break
            self.items[index], self.items[parent] = (
                self.items[parent],
                self.items[index],
            )
            index = parent

    def _heapify_down(self, index):
        length = len(self.items)
        while True:
            left = index * 2 + 1
            right = index * 2 + 2
            smallest = index

            if left < length and self._is_less(
                self.items[left], self.items[smallest]
            ):
                smallest = left
            if right < length and self._is_less(
                self.items[right], self.items[smallest]
            ):
                smallest = right
            if smallest == index:
                return

            self.items[index], self.items[smallest] = (
                self.items[smallest],
                self.items[index],
            )
            index = smallest

    @staticmethod
    def _is_less(left, right):
        if left.expire_at != right.expire_at:
            return left.expire_at < right.expire_at
        return left.key < right.key

