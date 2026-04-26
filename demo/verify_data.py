import http.client, json, time

def api(method, path, body=None):
    c = http.client.HTTPConnection("127.0.0.1", 18789, timeout=10)
    if body:
        c.request(method, path, json.dumps(body), {"Content-Type": "application/json"})
    else:
        c.request(method, path)
    r = c.getresponse()
    data = json.loads(r.read().decode())
    c.close()
    return data

print("1. Starting pipeline...")
d = api("POST", "/api/v1/pipelines", {"template": "20bit_tunable_coupler"})
pid = d["pipeline_id"]
print("   PID:", pid)

print("2. Waiting...")
for i in range(40):
    time.sleep(3)
    p = api("GET", "/api/v1/pipelines/" + pid)
    s = p["status"]
    n = len(p.get("steps", []))
    t = str((i+1)*3) + "s"
    print("  ", t, s, n, "steps")
    if s in ("completed", "aborted", "failed"):
        break

print("3. Final:", p["status"], len(p.get("steps", [])), "steps")

print("4. Checking data platform...")
te = api("GET", "/api/v1/dataplatform/training-export")
stats = te["dataset"]["stats"]
print("   Pipelines:", stats["total_pipelines"])
print("   Steps:", stats["total_steps"])
print("   Domains:", stats["domains"])

runs = te["dataset"].get("pipeline_runs", [])
if runs:
    r0 = runs[0]
    print("5. Pipeline record keys:", list(r0.keys()))
    print("   Name:", r0.get("name"))
    print("   Status:", r0.get("status"))
    print("   Total steps:", r0.get("total_steps"))

steps = te["dataset"].get("steps", [])
if steps:
    print("6. Step records:", len(steps))
    s0 = steps[0]
    print("   Step keys:", list(s0.keys()))
    print("   Sample step:", s0.get("agent"), "-", s0.get("title"))
print("Done!")
