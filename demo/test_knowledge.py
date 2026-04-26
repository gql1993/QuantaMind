from quantamind.server import knowledge_base as kb

stats = kb.get_stats()
print("Entries:", stats["total_entries"], "from", len(stats["sources"]), "sources")
for src, cnt in list(stats["sources"].items())[:8]:
    print(f"  {src}: {cnt}")

print("\n--- Search: 耦合器频率 ---")
for r in kb.search("耦合器频率", 3):
    print(f"  [{r['score']}] {r['source']}: {r['title'][:50]}")

print("\n--- Search: 约瑟夫森结 ---")
for r in kb.search("约瑟夫森结", 3):
    print(f"  [{r['score']}] {r['source']}: {r['title'][:50]}")

print("\n--- Search: CPW 共面波导 阻抗 ---")
for r in kb.search("CPW 共面波导 阻抗", 3):
    print(f"  [{r['score']}] {r['source']}: {r['title'][:50]}")
