import json, os

log_path = r"C:\Users\Admin\.gemini\antigravity-ide\brain\f5d99138-f728-422d-bf44-86703752c070\.system_generated\tasks\task-42.log"
out_path = r"d:\AI\AI content factory - v3.7B\Content Factory\vault\.extraction_runs\books\whats-going-on-in-there_2026-07-15\session_1\mapper_raw.md"

with open(log_path, "r", encoding="utf-8") as f:
    text = f.read()

# find the first '{'
idx = text.find('{')
if idx != -1:
    text = text[idx:]

data = json.loads(text)
answer = data["value"]["answer"] if "value" in data else data["answer"]

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    f.write(answer)
print("Success")
