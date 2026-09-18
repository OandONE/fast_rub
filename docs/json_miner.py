import json

files = [
    "methods",
    "models",
    "features"
]

def create_min(name_file: str):
    with open(f"{name_file}.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(f"{name_file}.min.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)

for file in files:
    create_min(file)

print("End")
