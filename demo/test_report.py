import http.client, json

c = http.client.HTTPConnection("127.0.0.1", 18789, timeout=10)
c.request("GET", "/api/v1/pipelines")
pls = json.loads(c.getresponse().read())
c.close()

print("Pipelines:", len(pls.get("pipelines", [])))
for p in pls.get("pipelines", []):
    pid = p["pipeline_id"]
    print(f"  {pid}: {p.get('name','')[:30]} ({p['status']}, {p['steps_count']} steps)")

    # 尝试下载 Word
    c2 = http.client.HTTPConnection("127.0.0.1", 18789, timeout=30)
    c2.request("GET", f"/api/v1/pipelines/{pid}/report?format=docx")
    r = c2.getresponse()
    print(f"    Word report: status={r.status}")
    if r.status != 200:
        body = r.read().decode("utf-8", errors="replace")[:500]
        print(f"    Error: {body}")
    else:
        data = r.read()
        print(f"    Size: {len(data)} bytes")
    c2.close()
    break  # 只测第一个
