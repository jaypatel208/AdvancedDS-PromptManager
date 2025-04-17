class ExtendibleHashTable:
    """
    Extendible hash table implementation that grows as needed
    and handles collisions using cuckoo hashing.
    """

    def __init__(self, initial_size=16):
        self.size = initial_size
        self.global_depth = 4  # Start with 2^4 = 16 buckets
        self.buckets = [[] for _ in range(self.size)]
        self.size_threshold = 0.75  # Load factor threshold

        # Two hash functions for cuckoo hashing
        self.hash1 = lambda key, size: hash(key) % size
        self.hash2 = lambda key, size: (hash(key) * 31) % size

    def _get_bucket_index(self, key):
        """Get the primary bucket index for a key."""
        return self.hash1(key, self.size)

    def _get_secondary_bucket_index(self, key):
        """Get the secondary bucket index for a key (used in cuckoo hashing)."""
        return self.hash2(key, self.size)

    def _resize(self):
        """Double the size of the hash table when load factor exceeds threshold."""
        old_buckets = self.buckets
        self.size *= 2
        self.global_depth += 1
        self.buckets = [[] for _ in range(self.size)]

        # Rehash all existing entries
        for bucket in old_buckets:
            for key, value in bucket:
                self._insert_with_cuckoo(key, value)

    def _insert_with_cuckoo(self, key, value, max_iterations=10):
        """Insert using cuckoo hashing to resolve collisions."""
        curr_key, curr_value = key, value
        for _ in range(max_iterations):
            # Try first hash function
            index = self.hash1(curr_key, self.size)

            # Check if bucket has space (we'll limit each bucket to 4 items)
            if len(self.buckets[index]) < 4:
                self.buckets[index].append((curr_key, curr_value))
                return True

            # Try second hash function
            index = self.hash2(curr_key, self.size)
            if len(self.buckets[index]) < 4:
                self.buckets[index].append((curr_key, curr_value))
                return True

            # Cuckoo: kick out an existing item and try to reinsert it
            index = self.hash1(curr_key, self.size)
            self.buckets[index].append((curr_key, curr_value))
            curr_key, curr_value = self.buckets[index].pop(0)

        # If we reach here, we've exceeded max iterations, need to resize
        self._resize()
        self._insert_with_cuckoo(curr_key, curr_value)
        return True

    def insert(self, key, value):
        """Insert a key-value pair into the hash table."""
        # Check if resizing is needed
        if (
            sum(len(bucket) for bucket in self.buckets) / self.size
            > self.size_threshold
        ):
            self._resize()

        # Try to find and update existing key
        for index in [self.hash1(key, self.size), self.hash2(key, self.size)]:
            for i, (k, _) in enumerate(self.buckets[index]):
                if k == key:
                    self.buckets[index][i] = (key, value)
                    return

        # Key doesn't exist, insert new key-value pair
        self._insert_with_cuckoo(key, value)

    def get(self, key, default=None):
        """Get the value associated with a key."""
        for index in [self.hash1(key, self.size), self.hash2(key, self.size)]:
            for k, v in self.buckets[index]:
                if k == key:
                    return v
        return default

    def delete(self, key):
        """Delete a key-value pair from the hash table."""
        for index in [self.hash1(key, self.size), self.hash2(key, self.size)]:
            for i, (k, _) in enumerate(self.buckets[index]):
                if k == key:
                    self.buckets[index].pop(i)
                    return True
        return False

    def keys(self):
        """Return all keys in the hash table."""
        keys = []
        for bucket in self.buckets:
            for k, _ in bucket:
                keys.append(k)
        return keys

    def items(self):
        """Return all key-value pairs in the hash table."""
        items = []
        for bucket in self.buckets:
            for k, v in bucket:
                items.append((k, v))
        return items
