"""通过 QuantaMind 分别设计 20 比特和 105 比特量子芯片"""
import http.client
import json
import time
import sys
import os

if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = ("127.0.0.1", 18789)

def chat(message):
    """发送对话并收集完整回复"""
    # 创建会话
    c = http.client.HTTPConnection(*BASE, timeout=10)
    c.request("POST", "/api/v1/sessions", json.dumps({}), {"Content-Type": "application/json"})
    sid = json.loads(c.getresponse().read())["session_id"]
    c.close()

    # 发送消息（非流式）
    c = http.client.HTTPConnection(*BASE, timeout=120)
    body = json.dumps({"session_id": sid, "message": message, "stream": False})
    c.request("POST", "/api/v1/chat", body, {"Content-Type": "application/json"})
    resp = c.getresponse().read().decode("utf-8", errors="replace")
    c.close()

    try:
        d = json.loads(resp)
        return d.get("content", resp[:500])
    except:
        return resp[:500]


print("=" * 70)
print("  QuantaMind 量子芯片设计 — 20 比特 + 105 比特")
print("=" * 70)

# 设计任务 1：20 比特
print("\n" + "=" * 50)
print("  任务 1：设计 20 比特可调耦合器量子芯片")
print("=" * 50)
msg1 = """请基于项目资料库中的 20 比特设计文档，使用 Qiskit Metal 设计一个 20 比特可调耦合器量子芯片：
1. 先查询 20 比特芯片规格（qeda_get_chip）
2. 查询约瑟夫森结参数（qeda_junction_params，SQUID 类型）
3. 用 Qiskit Metal 创建 12.5mm x 12.5mm 设计
4. 添加 5 个 Xmon 比特（使用真实频率参数）
5. 添加路由
6. 导出 GDS"""

print("发送中...")
reply1 = chat(msg1)
print("\n回复：")
print(reply1[:2000])

# 设计任务 2：105 比特
print("\n" + "=" * 50)
print("  任务 2：设计 105 比特可调耦合器量子芯片")
print("=" * 50)
msg2 = """请基于项目资料库中的 105 比特设计文档，查询 105 比特芯片规格并给出设计方案：
1. 查询 105 比特芯片规格（qeda_get_chip，chip_key=105bit）
2. 搜索知识库中关于 105 比特二维网格结构的设计要点（search_knowledge）
3. 查询约瑟夫森结参数
4. 用 Qiskit Metal 创建设计，添加前 5 个比特作为示例
5. 给出 105 比特完整设计方案总结"""

print("发送中...")
reply2 = chat(msg2)
print("\n回复：")
print(reply2[:2000])

print("\n" + "=" * 70)
print("  两个设计任务完成！可在 Web 界面查看对话流水线详情。")
print("=" * 70)
