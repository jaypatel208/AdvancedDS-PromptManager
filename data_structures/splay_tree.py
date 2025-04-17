class SplayTreeNode:
    def __init__(self, key, value=None):
        self.key = key  # timestamp
        self.value = value  # prompt_id
        self.left = None
        self.right = None


class SplayTree:
    """
    Splay Tree implementation for recency-based ranking of prompts.
    Automatically brings recently accessed elements to the root.
    """

    def __init__(self):
        self.root = None

    def _right_rotate(self, x):
        y = x.left
        x.left = y.right
        y.right = x
        return y

    def _left_rotate(self, x):
        y = x.right
        x.right = y.left
        y.left = x
        return y

    def _splay(self, root, key):
        """Bring the node with key to the root."""
        if root is None or root.key == key:
            return root

        if root.key > key:
            # Key is in left subtree
            if root.left is None:
                return root

            if root.left.key > key:
                # Zig-Zig (left left)
                root.left.left = self._splay(root.left.left, key)
                root = self._right_rotate(root)
            elif root.left.key < key:
                # Zig-Zag (left right)
                root.left.right = self._splay(root.left.right, key)
                if root.left.right:
                    root.left = self._left_rotate(root.left)

            # One more rotation if left child exists
            if root.left is None:
                return root
            else:
                return self._right_rotate(root)
        else:
            # Key is in right subtree
            if root.right is None:
                return root

            if root.right.key > key:
                # Zag-Zig (right left)
                root.right.left = self._splay(root.right.left, key)
                if root.right.left:
                    root.right = self._right_rotate(root.right)
            elif root.right.key < key:
                # Zag-Zag (right right)
                root.right.right = self._splay(root.right.right, key)
                root = self._left_rotate(root)

            # One more rotation if right child exists
            if root.right is None:
                return root
            else:
                return self._left_rotate(root)

    def search(self, key):
        """Search for a key and splay it to the root."""
        self.root = self._splay(self.root, key)
        if self.root and self.root.key == key:
            return self.root.value
        return None

    def insert(self, key, value):
        """Insert a new key-value pair and splay it to the root."""
        if not self.root:
            self.root = SplayTreeNode(key, value)
            return

        # Splay the key to bring it to root if it exists
        self.root = self._splay(self.root, key)

        # If key already exists, update value
        if self.root.key == key:
            self.root.value = value
            return

        # Create new node
        new_node = SplayTreeNode(key, value)

        # Insert new node
        if self.root.key > key:
            new_node.right = self.root
            new_node.left = self.root.left
            self.root.left = None
        else:
            new_node.left = self.root
            new_node.right = self.root.right
            self.root.right = None

        self.root = new_node

    def delete(self, key):
        """Delete a node with the given key."""
        if not self.root:
            return

        # Splay the key to bring it to root if it exists
        self.root = self._splay(self.root, key)

        # If key doesn't exist
        if self.root.key != key:
            return

        # If key exists at root
        if not self.root.left:
            self.root = self.root.right
        elif not self.root.right:
            self.root = self.root.left
        else:
            # Find the successor
            temp = self.root.right
            while temp.left:
                temp = temp.left

            # Splay successor to the root of right subtree
            self.root.right = self._splay(self.root.right, temp.key)

            # Link left subtree as left child of successor
            self.root.right.left = self.root.left
            self.root = self.root.right

    def get_recent(self, n=10):
        """Get the n most recent prompts (largest keys)."""
        result = []

        def _inorder_reverse(node):
            if not node or len(result) >= n:
                return

            _inorder_reverse(
                node.right
            )  # Visit right subtree first for descending order

            if len(result) < n:
                result.append((node.key, node.value))

            _inorder_reverse(node.left)

        _inorder_reverse(self.root)
        return result
