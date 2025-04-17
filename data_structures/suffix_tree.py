class SuffixTreeNode:
    def __init__(self):
        self.children = {}
        self.indices = []  # Store indices of original strings


class SuffixTree:
    """
    Suffix Tree implementation for efficient substring searching.
    """

    def __init__(self):
        self.root = SuffixTreeNode()
        self.texts = []  # Original texts

    def insert(self, text, text_id):
        """Insert a text and build its suffix tree."""
        self.texts.append((text, text_id))
        text_index = len(self.texts) - 1

        # Insert all suffixes
        for i in range(len(text)):
            suffix = text[i:]
            node = self.root

            for char in suffix:
                if char not in node.children:
                    node.children[char] = SuffixTreeNode()
                node = node.children[char]
                node.indices.append((text_index, text_id))

    def search(self, substring):
        """Search for a substring and return associated text IDs."""
        node = self.root

        # Traverse the tree to find the substring
        for char in substring:
            if char not in node.children:
                return []
            node = node.children[char]

        # Return unique text IDs
        return list(set(text_id for _, text_id in node.indices))

    def get_text(self, text_index):
        """Get the original text by its index."""
        if 0 <= text_index < len(self.texts):
            return self.texts[text_index]
        return None

    def delete(self, text_id):
        """Delete a text and its suffixes from the tree."""
        # Find the index of the text to delete
        text_index = None
        for i, (_, tid) in enumerate(self.texts):
            if tid == text_id:
                text_index = i
                break

        if text_index is None:
            return False

        # Mark as deleted (this is simpler than actually rebuilding the tree)
        self.texts[text_index] = ("", text_id)

        # Remove references in the tree
        def remove_references(node):
            node.indices = [
                (idx, tid) for idx, tid in node.indices if idx != text_index
            ]
            for child in node.children.values():
                remove_references(child)

        remove_references(self.root)
        return True
