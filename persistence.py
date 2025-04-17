import os
import pickle
from datetime import datetime


class PersistentDataManager:
    """
    Handles persistence of prompt data between sessions.
    Implements a simple persistent data structure concept by storing
    incremental changes.
    """

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.file_path = os.path.join(data_dir, "prompt_store.pkl")

        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # Initialize data structures
        self.data = {
            "prompts": {},  # Prompt data
            "tags": {},  # Tag to prompt mapping
            "usage": {},  # Prompt usage counts
            "timestamps": {},  # Last accessed timestamps
            "version": 0,  # Data version
        }

        # Load data if it exists
        self.load()

    def load(self):
        """Load data from persistent storage."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "rb") as f:
                    self.data = pickle.load(f)
            except (pickle.PickleError, EOFError):
                # Handle corrupted pickle file
                print("Warning: Could not load data file, starting with empty data.")

    def save(self):
        """Save data to persistent storage."""
        # Increment version
        self.data["version"] += 1

        # Save to file
        with open(self.file_path, "wb") as f:
            pickle.dump(self.data, f)

    def add_prompt(self, prompt_id, prompt_text, tags=None):
        """Add a new prompt or update an existing one."""
        if tags is None:
            tags = []

        # Store prompt data
        current_time = datetime.now().timestamp()
        self.data["prompts"][prompt_id] = {
            "text": prompt_text,
            "tags": tags,
            "created_at": current_time,
            "modified_at": current_time,
        }

        # Update tag mappings
        for tag in tags:
            if tag not in self.data["tags"]:
                self.data["tags"][tag] = []
            if prompt_id not in self.data["tags"][tag]:
                self.data["tags"][tag].append(prompt_id)

        # Initialize usage count if new
        if prompt_id not in self.data["usage"]:
            self.data["usage"][prompt_id] = 0

        # Update timestamp
        self.data["timestamps"][prompt_id] = current_time

        # Save changes
        self.save()

    def get_prompt(self, prompt_id):
        """Get a prompt by ID."""
        if prompt_id in self.data["prompts"]:
            # Update timestamp for recency tracking
            self.data["timestamps"][prompt_id] = datetime.now().timestamp()
            return self.data["prompts"][prompt_id]
        return None

    def delete_prompt(self, prompt_id):
        """Delete a prompt."""
        if prompt_id in self.data["prompts"]:
            # Remove tags associations
            for tag in self.data["prompts"][prompt_id]["tags"]:
                if tag in self.data["tags"] and prompt_id in self.data["tags"][tag]:
                    self.data["tags"][tag].remove(prompt_id)
                    # Clean up empty tag lists
                    if not self.data["tags"][tag]:
                        del self.data["tags"][tag]

            # Remove prompt and associated data
            del self.data["prompts"][prompt_id]
            if prompt_id in self.data["usage"]:
                del self.data["usage"][prompt_id]
            if prompt_id in self.data["timestamps"]:
                del self.data["timestamps"][prompt_id]

            # Save changes
            self.save()
            return True
        return False

    def record_usage(self, prompt_id):
        """Record that a prompt has been used."""
        if prompt_id in self.data["prompts"]:
            # Increment usage count
            if prompt_id not in self.data["usage"]:
                self.data["usage"][prompt_id] = 0
            self.data["usage"][prompt_id] += 1

            # Update timestamp
            self.data["timestamps"][prompt_id] = datetime.now().timestamp()

            # Save changes
            self.save()
            return True
        return False

    def get_all_prompts(self):
        """Get all prompts."""
        result = {}
        for prompt_id, prompt_data in self.data["prompts"].items():
            result[prompt_id] = {
                **prompt_data,
                "usage_count": self.data["usage"].get(prompt_id, 0),
                "last_accessed": self.data["timestamps"].get(prompt_id, 0),
            }
        return result

    def get_prompts_by_tag(self, tag):
        """Get all prompts with a specific tag."""
        if tag in self.data["tags"]:
            return [
                prompt_id
                for prompt_id in self.data["tags"][tag]
                if prompt_id in self.data["prompts"]
            ]
        return []

    def get_most_used_prompts(self, limit=10):
        """Get the most frequently used prompts."""
        # Create list of (prompt_id, count) tuples
        usage_items = [
            (pid, count)
            for pid, count in self.data["usage"].items()
            if pid in self.data["prompts"]
        ]

        # Sort by count in descending order
        sorted_items = sorted(usage_items, key=lambda x: x[1], reverse=True)

        # Return top N items
        return sorted_items[:limit]

    def get_recent_prompts(self, limit=10):
        """Get the most recently used prompts."""
        # Create list of (prompt_id, timestamp) tuples
        timestamp_items = [
            (pid, ts)
            for pid, ts in self.data["timestamps"].items()
            if pid in self.data["prompts"]
        ]

        # Sort by timestamp in descending order
        sorted_items = sorted(timestamp_items, key=lambda x: x[1], reverse=True)

        # Return top N items
        return [(pid, self.data["prompts"][pid]) for pid, _ in sorted_items[:limit]]

    def get_all_tags(self):
        """Get all tags and their prompt counts."""
        return {tag: len(prompts) for tag, prompts in self.data["tags"].items()}
