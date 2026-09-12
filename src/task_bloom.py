"""Bloom filter for fast membership checks."""
import hashlib
import math
from typing import List


class BloomFilter:
    """A probabilistic set for fast membership checks."""
    def __init__(self, expected_items: int = 10000, false_positive_rate: float = 0.01):
        self._size = self._optimal_size(expected_items, false_positive_rate)
        self._hash_count = self._optimal_hashes(expected_items, self._size)
        self._bits = [False] * self._size
        self._count = 0

    @staticmethod
    def _optimal_size(n: int, p: float) -> int:
        """m = -(n * ln(p)) / (ln(2)^2)"""
        if n <= 0 or p <= 0 or p >= 1:
            return 1024
        return max(64, int(-(n * math.log(p)) / (math.log(2) ** 2)))

    @staticmethod
    def _optimal_hashes(n: int, m: int) -> int:
        """k = (m/n) * ln(2)"""
        if n <= 0:
            return 3
        return max(1, min(30, int((m / n) * math.log(2))))

    def _hashes(self, item) -> List[int]:
        """Generate k hash positions for an item."""
        data = str(item).encode("utf-8")
        positions = []
        for i in range(self._hash_count):
            h = hashlib.sha256(data + bytes([i])).hexdigest()
            positions.append(int(h, 16) % self._size)
        return positions

    def add(self, item):
        """Add an item to the filter."""
        for pos in self._hashes(item):
            self._bits[pos] = True
        self._count += 1

    def contains(self, item) -> bool:
        """Check if item is PROBABLY in the set (may be false positive)."""
        return all(self._bits[pos] for pos in self._hashes(item))

    def count(self) -> int:
        """Number of items added."""
        return self._count

    def bit_size(self) -> int:
        return self._size

    def hash_count(self) -> int:
        return self._hash_count

    def estimated_false_positive_rate(self) -> float:
        """Estimate current false positive rate."""
        if self._count == 0:
            return 0.0
        set_bits = sum(1 for b in self._bits if b)
        return (set_bits / self._size) ** self._hash_count

    def clear(self):
        self._bits = [False] * self._size
        self._count = 0

    def saturation(self) -> float:
        """Fraction of bits set."""
        set_bits = sum(1 for b in self._bits if b)
        return round(set_bits / self._size, 4)

    @classmethod
    def from_items(cls, items, false_positive_rate: float = 0.01) -> "BloomFilter":
        """Create a filter pre-populated with items."""
        bf = cls(expected_items=max(len(items), 1), false_positive_rate=false_positive_rate)
        for item in items:
            bf.add(item)
        return bf


def bloom_report(bf: BloomFilter) -> dict:
    return {"count": bf.count(), "bit_size": bf.bit_size(),
            "hash_count": bf.hash_count(),
            "saturation": bf.saturation(),
            "estimated_fp_rate": round(bf.estimated_false_positive_rate(), 6)}
