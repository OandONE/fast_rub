import json

files = [
    "methods",
    "models",
    "features",
    "pyrubi",
    "prerequisites"
]

datas = {}

def create_min(name_file: str):
    with open(f"{name_file}.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    datas[name_file] = data
    with open(f"{name_file}.min.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)

def create_all():
    with open(f"all.json", 'w', encoding='utf-8') as f:
        json.dump(datas, f, ensure_ascii=False, indent=4)
    with open(f"all.min.json", 'w', encoding='utf-8') as f:
        json.dump(datas, f, separators=(',', ':'), ensure_ascii=False)

def main():

    for file in files:
        create_min(file)

    create_all()

    print("End")

main()
