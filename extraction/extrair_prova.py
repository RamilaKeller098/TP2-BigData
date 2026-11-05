import fitz

PDF_PATH = "extraction/2023_PV_engenharia_da_computacao.pdf"

doc = fitz.open(PDF_PATH)

print("PDF aberto com sucesso.")
print(f"Quantidade de paginas: {len(doc)}")

print("\n===== PRIMEIRA PAGINA =====")
print(doc[0].get_text())

doc.close()