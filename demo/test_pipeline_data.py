"""测试流水线运行并验证数据保存到数据中台"""
import json, time, urllib.request

BASE = "http://127.0.0.1:18789"

def api(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

print("1. 启动流水线...")
d = api("POST", "/api/v1/pipelines", {"template": "20bit_tunable_coupler"})
pid = d["pipeline_id"]
print(f"   Pipeline ID: {pid}")

print("2. 等待完成...")
for i in range(120):
    time.sleep(2)
    p = api("GET", f"/api/v1/pipelines/{pid}")
    steps = len(p.get("steps", []))
    status = p["status"]
    print(f"   [{i*2:3d}s] status={status} steps={steps}")
    if status in ("completed", "aborted", "failed"):
        break

print(f"\n3. 最终状态: {p['status']}, 共 {len(p['steps'])} 步")
completed = sum(1 for s in p["steps"] if s["status"] == "completed")
failed = sum(1 for s in p["steps"] if s["status"] == "failed")
print(f"   完成: {completed}, 失败: {failed}")

print("\n4. 检查数据中台...")
te = api("GET", "/api/v1/dataplatform/training-export")
stats = te.get("dataset", {}).get("stats", {})
print(f"   流水线记录: {stats.get('total_pipelines', 0)}")
print(f"   步骤记录: {stats.get('total_steps', 0)}")
print(f"   数据域: {stats.get('domains', [])}")

hist = api("GET", "/api/v1/dataplatform/pipeline-history")
print(f"   历史记录数: {hist.get('total', 0)}")
for r in hist.get("records", []):
    print(f"     {r['pipeline_id']}: {r['status']} ({r.get('completed_steps',0)}/{r.get('total_steps',0)})")

print("\n5. 数据导出样本:")
ds = te.get("dataset", {})
pl_runs = ds.get("pipeline_runs", [])
if pl_runs:
    print(f"   pipeline_runs[0] keys: {list(pl_runs[0].keys())}")
step_recs = ds.get("steps", [])
if step_recs:
    print(f"   steps[0] keys: {list(step_recs[0].keys())}")
    print(f"   steps 总数: {len(step_recs)}")

print("\nDone!")
