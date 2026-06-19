import os
import json

run_folder = r"d:\AI\AI content factory - v3.7B\.extraction_runs\good-inside_2026-05-21"

context = {
    "source_acronym": "GI",
    "book_meta": {
        "book_name": "Good Inside",
        "author": "Dr. Becky Kennedy",
        "year": "2022"
    },
    "book_topics": ["parenting", "child-psychology"],
    "chunk_topics_map": {}
}

# we have chunks 2..31 except 1?
for i in list(range(2, 32)):
    context["chunk_topics_map"][str(i)] = ["child-behavior", "emotional-regulation"]

with open(os.path.join(run_folder, "atomizer_context.json"), "w", encoding="utf-8") as f:
    json.dump(context, f, indent=4)

print("Atomizer context created.")
