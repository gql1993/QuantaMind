"""通过 QuantaMind 分别设计 20 比特、100 比特、105 比特量子芯片"""
import http.client
import json
import sys
import os
import time

if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def chat(message, timeout=180):
    c = http.client.HTTPConnection("127.0.0.1", 18789, timeout=10)
    c.request("POST", "/api/v1/sessions", json.dumps({}), {"Content-Type": "application/json"})
    sid = json.loads(c.getresponse().read())["session_id"]
    c.close()
    c = http.client.HTTPConnection("127.0.0.1", 18789, timeout=timeout)
    c.request("POST", "/api/v1/chat", json.dumps({"session_id": sid, "message": message, "stream": False}), {"Content-Type": "application/json"})
    resp = c.getresponse().read().decode("utf-8", errors="replace")
    c.close()
    try:
        return json.loads(resp).get("content", resp[:1000])
    except:
        return resp[:1000]

print("=" * 70)
print("  QuantaMind 三款量子芯片设计任务")
print("=" * 70)

tasks = [
    ("20 比特可调耦合器芯片", """请设计 20 比特可调耦合器量子芯片：
1. 先调用 qeda_catalog 查看设计团队的资料目录
2. 调用 qeda_get_chip（chip_key=20bit）获取真实设计参数
3. 调用 qeda_junction_params（jj_type=Squid_Manhattan）获取 SQUID 约瑟夫森结参数
4. 用 metal_create_design 创建 12.5mm x 12.5mm 设计
5. 用 qeda_get_qubit 查询 Q1-Q5 的频率，然后用 metal_add_transmon 添加这 5 个比特
6. 用 metal_add_route 添加 Q1-Q2 和 Q2-Q3 的路由
7. 用 metal_export_gds 导出 GDS
8. 总结设计方案"""),

    ("100 比特芯片", """请基于 QEDA 团队资料设计 100 比特量子芯片：
1. 调用 qeda_catalog 查看 100 比特设计规范
2. 调用 search_knowledge 搜索"100比特 设计规范 指标"获取设计要求
3. 调用 qeda_junction_params 获取约瑟夫森结参数
4. 用 metal_create_design 创建设计
5. 添加 3 个示例比特
6. 基于设计规范给出 100 比特完整设计方案建议"""),

    ("105 比特可调耦合器芯片", """请设计 105 比特可调耦合器量子芯片：
1. 调用 qeda_get_chip（chip_key=105bit）获取 105 比特完整规格
2. 调用 search_knowledge 搜索"105比特 二维网格 谐振腔"
3. 调用 qeda_get_qubit（chip_key=105bit，qubit_id=Q001）查看第一个比特的详细参数
4. 用 metal_create_design 创建设计
5. 添加 Q001-Q005 五个比特（使用真实频率）
6. 导出 GDS
7. 总结 105 比特设计方案，对比设计目标"""),
]

for i, (name, prompt) in enumerate(tasks):
    print(f"\n{'='*60}")
    print(f"  任务 {i+1}/3：{name}")
    print(f"{'='*60}")
    print("发送中...")
    t0 = time.time()
    reply = chat(prompt)
    dt = time.time() - t0
    print(f"耗时：{dt:.1f}s")
    print(f"\n{reply[:3000]}")
    if len(reply) > 3000:
        print(f"\n... (共 {len(reply)} 字符)")

print(f"\n{'='*70}")
print("  三款芯片设计任务完成！")
print("  在 Web 界面「流水线」页查看 3 条对话流水线的详细步骤。")
print(f"{'='*70}")
