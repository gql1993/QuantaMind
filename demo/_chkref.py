from docx import Document
doc = Document(r"E:\work\QuantaMind\docs\QuantaMind_Paper_LNCS_v5.docx")
count = 0
for p in doc.paragraphs:
    if p.style and p.style.name == "referenceitem" and p.text.strip():
        count += 1
        print(f"  [{count}] {p.text[:100]}")
print(f"\nTotal: {count}")
