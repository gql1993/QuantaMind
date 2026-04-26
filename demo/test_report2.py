"""直接调用报告生成函数看错误"""
import sys, traceback
sys.path.insert(0, ".")
from quantamind.agents.orchestrator import chat_pipelines

print("Chat pipelines:", len(chat_pipelines))
for pid, p in chat_pipelines.items():
    print(f"  {pid}: {len(p.get('steps',[]))} steps, status={p['status']}")

    # 模拟报告生成
    try:
        from quantamind.server.result_explain import explain
        stages_map = {s["stage"]: s for s in p.get("stages", [])}
        for step in p.get("steps", [])[:3]:
            print(f"    Step: {step.get('tool','?')}")
            exp = explain(step.get("tool", ""), step.get("args", {}), step.get("result", {}))
            print(f"      OK: {exp.get('explanation','')[:60]}")
    except Exception as e:
        traceback.print_exc()
        break

    # 尝试 Word 生成
    try:
        from quantamind.server.gateway import _generate_word_report
        result = _generate_word_report(pid, p, stages_map, explain)
        print(f"    Word: OK ({type(result)})")
    except Exception as e:
        print(f"    Word ERROR: {e}")
        traceback.print_exc()
    break
