from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn
import uuid
import time
from datetime import datetime
from data_structures.hash_table import ExtendibleHashTable
from data_structures.trie import CompressedTrie
from data_structures.suffix_tree import SuffixTree
from data_structures.heap import MaxHeap
from data_structures.splay_tree import SplayTree

# Import our data structures
# from data_structures import (
#     ExtendibleHashTable,
#     CompressedTrie,
#     SuffixTree,
#     MaxHeap,
#     SplayTree,
# )
from persistence import PersistentDataManager

app = FastAPI(title="AI Prompt Manager")
templates = Jinja2Templates(directory="templates")

# Initialize data structures
data_manager = PersistentDataManager()
prompt_hash = ExtendibleHashTable()  # For fast prompt lookup
tag_trie = CompressedTrie()  # For tag-based autocomplete
text_index = SuffixTree()  # For substring/full-text search
usage_heap = MaxHeap()  # For tracking most-used prompts
recency_tree = SplayTree()  # For recency-based ranking


# Load data from persistent storage into our data structures
def initialize_data_structures():
    prompts = data_manager.get_all_prompts()
    for prompt_id, prompt_data in prompts.items():
        # Update hash table
        prompt_hash.insert(prompt_id, prompt_data)

        # Update text search index
        text_index.insert(prompt_data["text"], prompt_id)

        # Update tag trie
        for tag in prompt_data["tags"]:
            tag_trie.insert(tag, prompt_id)

        # Update usage heap
        usage_heap.insert(prompt_id, prompt_data["usage_count"])

        # Update recency tree
        timestamp = prompt_data.get('last_accessed', prompt_data['created_at'])
        recency_tree.insert(timestamp, prompt_id)


# Call initialization on startup
@app.on_event("startup")
async def startup_event():
    initialize_data_structures()


# Root route
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    most_used = usage_heap.get_top(5)
    most_used_data = []
    for prompt_id, count in most_used:
        prompt_data = prompt_hash.get(prompt_id)
        if prompt_data:
            most_used_data.append(
                {
                    "id": prompt_id,
                    "text": (
                        prompt_data["text"][:50] + "..."
                        if len(prompt_data["text"]) > 50
                        else prompt_data["text"]
                    ),
                    "count": count,
                    "tags": prompt_data["tags"],
                }
            )

    recent_data = []
    recent_prompts = recency_tree.get_recent(5)
    for _, prompt_id in recent_prompts:
        prompt_data = prompt_hash.get(prompt_id)
        if prompt_data:
            recent_data.append(
                {
                    "id": prompt_id,
                    "text": (
                        prompt_data["text"][:50] + "..."
                        if len(prompt_data["text"]) > 50
                        else prompt_data["text"]
                    ),
                    "last_accessed": datetime.fromtimestamp(
                        prompt_data["last_accessed"]
                    ).strftime("%Y-%m-%d %H:%M"),
                    "tags": prompt_data["tags"],
                }
            )

    all_tags = data_manager.get_all_tags()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "most_used": most_used_data,
            "recent": recent_data,
            "all_tags": all_tags,
        },
    )


# Add a new prompt
@app.post("/add-prompt")
async def add_prompt(prompt_text: str = Form(...), tags: str = Form("")):
    # Generate a unique ID
    prompt_id = str(uuid.uuid4())

    # Process tags (comma-separated)
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    # Add to persistence manager
    data_manager.add_prompt(prompt_id, prompt_text, tag_list)

    # Update our in-memory data structures
    prompt_data = data_manager.get_prompt(prompt_id)

    # Update hash table
    prompt_hash.insert(prompt_id, prompt_data)

    # Update text search index
    text_index.insert(prompt_text, prompt_id)

    # Update tag trie
    for tag in tag_list:
        tag_trie.insert(tag, prompt_id)

    # Update usage heap (new prompts start with 0 usage)
    usage_heap.insert(prompt_id, 0)

    # Add this before the insert operation
    if "last_accessed" not in prompt_data:
        # Add the current timestamp as last_accessed
        prompt_data["last_accessed"] = time.time()

    # Update recency tree
    recency_tree.insert(prompt_data['created_at'], prompt_id)

    return RedirectResponse(url="/", status_code=303)


# Search prompts
@app.get("/search")
async def search(request: Request, q: str = "", tag: str = ""):
    results = []

    if tag:
        # Search by tag
        matching_prompts = tag_trie.starts_with(tag)
        for _, prompt_id in matching_prompts:
            prompt_data = prompt_hash.get(prompt_id)
            if prompt_data:
                results.append(
                    {
                        "id": prompt_id,
                        "text": prompt_data["text"],
                        "tags": prompt_data["tags"],
                        "usage_count": data_manager.data["usage"].get(prompt_id, 0),
                    }
                )
    elif q:
        # Full-text search
        matching_ids = text_index.search(q)
        for prompt_id in matching_ids:
            prompt_data = prompt_hash.get(prompt_id)
            if prompt_data:
                results.append(
                    {
                        "id": prompt_id,
                        "text": prompt_data["text"],
                        "tags": prompt_data["tags"],
                        "usage_count": data_manager.data["usage"].get(prompt_id, 0),
                    }
                )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "search_results": results,
            "search_query": q,
            "search_tag": tag,
            "all_tags": data_manager.get_all_tags(),
        },
    )


# Get tag suggestions (for autocomplete)
@app.get("/tags/suggest")
async def suggest_tags(prefix: str = ""):
    suggestions = []
    if prefix:
        matches = tag_trie.starts_with(prefix)
        for tag, _ in matches:
            if tag not in suggestions:
                suggestions.append(tag)

    return {"suggestions": suggestions[:10]}  # Limit to 10 suggestions


# Use a prompt (increment usage count)
@app.post("/use-prompt/{prompt_id}")
async def use_prompt(prompt_id: str):
    # Update persistence layer
    success = data_manager.record_usage(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Update our in-memory data structures
    prompt_data = data_manager.get_prompt(prompt_id)
    usage_count = data_manager.data["usage"].get(prompt_id, 0)

    # Update usage heap
    usage_heap.increment(prompt_id)

    # Add this before the insert operation
    if "last_accessed" not in prompt_data:
        # Add the current timestamp as last_accessed
        prompt_data["last_accessed"] = time.time()

    # Update recency tree
    recency_tree.insert(prompt_data["last_accessed"], prompt_id)

    return {"success": True, "usage_count": usage_count}


# Delete a prompt
@app.delete("/prompt/{prompt_id}")
async def delete_prompt(prompt_id: str):
    # Get prompt data before deletion
    prompt_data = prompt_hash.get(prompt_id)
    if not prompt_data:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Delete from persistence layer
    success = data_manager.delete_prompt(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Failed to delete prompt")

    # Update our in-memory data structures

    # Remove from hash table
    prompt_hash.delete(prompt_id)

    # Remove from text search index
    text_index.delete(prompt_id)

    # Remove from tag trie
    for tag in prompt_data["tags"]:
        tag_trie.delete(tag, prompt_id)

    # Remove from usage heap
    usage_heap.remove(prompt_id)

    # Remove from recency tree (we'd need the timestamp)
    if "last_accessed" in prompt_data:
        recency_tree.delete(prompt_data["last_accessed"])

    return {"success": True}


# View a specific prompt
@app.get("/prompt/{prompt_id}", response_class=HTMLResponse)
async def view_prompt(request: Request, prompt_id: str):
    prompt_data = prompt_hash.get(prompt_id)
    if not prompt_data:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Record this view as a usage
    data_manager.record_usage(prompt_id)
    usage_count = data_manager.data["usage"].get(prompt_id, 0)

    # Update our in-memory data structures
    usage_heap.increment(prompt_id)
    recency_tree.insert(prompt_data["last_accessed"], prompt_id)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "viewing_prompt": {
                "id": prompt_id,
                "text": prompt_data["text"],
                "tags": prompt_data["tags"],
                "usage_count": usage_count,
                "created_at": datetime.fromtimestamp(
                    prompt_data["created_at"]
                ).strftime("%Y-%m-%d %H:%M"),
                "last_accessed": datetime.fromtimestamp(
                    prompt_data["last_accessed"]
                ).strftime("%Y-%m-%d %H:%M"),
            },
            "all_tags": data_manager.get_all_tags(),
        },
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
