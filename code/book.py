data = [
    {"oim": ""},
    {"login": "booted"},
    {"login1": "booted"},
    {"login2": "booted"},
    {"login3": "booted"}
]

# Collect only the keys from dicts that meet the criteria
a = [
    key for item in data
    if "oim" not in item and all(value != "booted" for value in item.values())
    for key in item.keys()
]

print(a)
