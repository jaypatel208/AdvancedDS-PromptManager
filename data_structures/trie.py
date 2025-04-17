class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.values = []  # Used to store prompt IDs associated with this tag


class CompressedTrie:
    """
    Compressed Trie implementation for efficient tag-based autocomplete.
    """

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, value=None):
        """Insert a word into the trie and associate it with a value."""
        node = self.root

        # Navigate to the proper position in the trie
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]

        node.is_end_of_word = True
        if value is not None and value not in node.values:
            node.values.append(value)

    def search(self, word):
        """Search for a word in the trie."""
        node = self.root

        # Navigate through the trie
        for char in word:
            if char not in node.children:
                return False, []
            node = node.children[char]

        return node.is_end_of_word, node.values

    def starts_with(self, prefix):
        """Find all words that start with a given prefix."""
        node = self.root

        # Navigate to the proper position in the trie
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        # Collect all words that start with the prefix
        results = []
        self._collect_words(node, prefix, results)
        return results

    def _collect_words(self, node, prefix, results):
        """Helper function for starts_with to collect all words with a given prefix."""
        if node.is_end_of_word:
            for value in node.values:
                results.append((prefix, value))

        # Recursively search all children
        for char, child_node in node.children.items():
            self._collect_words(child_node, prefix + char, results)

    def delete(self, word, value=None):
        """Delete a word from the trie."""

        def _delete_helper(node, word, index, value):
            # Base case: we've processed all characters
            if index == len(word):
                # If this is the end of a word
                if node.is_end_of_word:
                    if value is None:
                        # Remove all values
                        node.values = []
                        node.is_end_of_word = len(node.values) > 0
                    elif value in node.values:
                        # Remove specific value
                        node.values.remove(value)
                        node.is_end_of_word = len(node.values) > 0

                # Check if we can delete this node
                return len(node.children) == 0 and not node.is_end_of_word

            # If character doesn't exist, word is not in trie
            char = word[index]
            if char not in node.children:
                return False

            # Recursively delete
            should_delete_child = _delete_helper(
                node.children[char], word, index + 1, value
            )

            # If child should be deleted
            if should_delete_child:
                del node.children[char]
                return len(node.children) == 0 and not node.is_end_of_word

            return False

        _delete_helper(self.root, word, 0, value)
