class MaxHeap:
    """
    Max Heap implementation for tracking most-used prompts.
    """

    def __init__(self):
        self.heap = []
        self.position_map = {}  # Maps prompt_id to position in heap

    def _parent(self, i):
        return (i - 1) // 2

    def _left(self, i):
        return 2 * i + 1

    def _right(self, i):
        return 2 * i + 2

    def _swap(self, i, j):
        """Swap elements and update position map."""
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.position_map[self.heap[i][0]] = i
        self.position_map[self.heap[j][0]] = j

    def _sift_up(self, i):
        """Move element up to maintain heap property."""
        parent = self._parent(i)
        if i > 0 and self.heap[i][1] > self.heap[parent][1]:
            self._swap(i, parent)
            self._sift_up(parent)

    def _sift_down(self, i):
        """Move element down to maintain heap property."""
        max_idx = i
        left = self._left(i)
        right = self._right(i)

        if left < len(self.heap) and self.heap[left][1] > self.heap[max_idx][1]:
            max_idx = left

        if right < len(self.heap) and self.heap[right][1] > self.heap[max_idx][1]:
            max_idx = right

        if i != max_idx:
            self._swap(i, max_idx)
            self._sift_down(max_idx)

    def insert(self, prompt_id, count):
        """Insert a prompt with its usage count."""
        # If prompt already exists, update its count
        if prompt_id in self.position_map:
            pos = self.position_map[prompt_id]
            old_count = self.heap[pos][1]
            self.heap[pos] = (prompt_id, count)

            # Determine if we need to sift up or down
            if count > old_count:
                self._sift_up(pos)
            else:
                self._sift_down(pos)
        else:
            # Add new prompt to heap
            self.heap.append((prompt_id, count))
            pos = len(self.heap) - 1
            self.position_map[prompt_id] = pos
            self._sift_up(pos)

    def get_top(self, n=10):
        """Get the top N most used prompts."""
        # Create a copy to avoid modifying the original heap
        temp_heap = list(self.heap)
        result = []

        for _ in range(min(n, len(temp_heap))):
            if not temp_heap:
                break

            # Extract max
            prompt_id, count = temp_heap[0]
            result.append((prompt_id, count))

            # Replace root with last element and sift down
            temp_heap[0] = temp_heap[-1]
            temp_heap.pop()

            # Sift down the new root
            i = 0
            while True:
                left = 2 * i + 1
                right = 2 * i + 2
                largest = i

                if left < len(temp_heap) and temp_heap[left][1] > temp_heap[largest][1]:
                    largest = left

                if (
                    right < len(temp_heap)
                    and temp_heap[right][1] > temp_heap[largest][1]
                ):
                    largest = right

                if largest != i:
                    temp_heap[i], temp_heap[largest] = temp_heap[largest], temp_heap[i]
                    i = largest
                else:
                    break

        return result

    def increment(self, prompt_id, increment_by=1):
        """Increment the usage count of a prompt."""
        if prompt_id in self.position_map:
            pos = self.position_map[prompt_id]
            current_count = self.heap[pos][1]
            self.insert(prompt_id, current_count + increment_by)
        else:
            self.insert(prompt_id, increment_by)

    def remove(self, prompt_id):
        """Remove a prompt from the heap."""
        if prompt_id not in self.position_map:
            return

        # Get position and replace with last element
        pos = self.position_map[prompt_id]
        last_pos = len(self.heap) - 1

        # Swap with last element
        self._swap(pos, last_pos)

        # Remove last element
        self.heap.pop()
        del self.position_map[prompt_id]

        # If we didn't remove the last element, fix heap structure
        if pos < last_pos:
            # Determine whether to sift up or down
            parent = self._parent(pos)
            if pos > 0 and self.heap[pos][1] > self.heap[parent][1]:
                self._sift_up(pos)
            else:
                self._sift_down(pos)
