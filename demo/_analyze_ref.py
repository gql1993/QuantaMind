from pypdf import PdfReader
import re

reader = PdfReader(r"E:\量子科技\凌浩工程\AI for quantum\AI加量子论文\El Agente An Autonomous Agent for Quantum.pdf")
print(f"Total pages: {len(reader.pages)}")

# Find max reference number
all_text = ""
for page in reader.pages:
    all_text += (page.extract_text() or "") + "\n"

refs = re.findall(r'\((\d+)\)', all_text)
if refs:
    nums = [int(r) for r in refs if int(r) < 200]
    print(f"Max ref number: {max(nums) if nums else 0}")

# Count figures and tables
figs = re.findall(r'Figure \d+', all_text)
tbls = re.findall(r'Table \d+', all_text)
print(f"Figure mentions: {len(set(figs))}, unique: {set(figs)}")
print(f"Table mentions: {len(set(tbls))}, unique: {set(tbls)}")

# Structure overview
for i in range(min(20, len(reader.pages))):
    txt = reader.pages[i].extract_text() or ""
    lines = [l.strip() for l in txt.split("\n") if l.strip() and len(l.strip()) < 100]
    for line in lines:
        upper_words = sum(1 for w in line.split() if w[0].isupper()) if line.split() else 0
        if upper_words >= len(line.split()) * 0.6 and len(line) > 10 and len(line) < 80:
            print(f"  p{i+1}: {line}")
