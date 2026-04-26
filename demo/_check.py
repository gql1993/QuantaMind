import urllib.request, json
d = json.loads(urllib.request.urlopen("http://127.0.0.1:18789/api/v1/agents").read())
for i, a in enumerate(d):
    print(f"  {i+1:2d}. {a['emoji']} {a['label']} ({a['role']})")
