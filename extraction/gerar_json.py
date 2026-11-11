import fitz
import re
import json

PDF_PATH = "extraction/2023_PV_engenharia_da_computacao.pdf"
OUTPUT_PATH = "extraction/questoes_extraidas.json"

doc = fitz.open(PDF_PATH)

questoes = {}
questao_atual = None
texto_atual = []
pagina_inicio = None

padrao_questao = re.compile(r"^QUESTÃO\s+(0?[1-9]|[12][0-9]|3[0-8])$")

for pagina_num, pagina in enumerate(doc, start=1):

    # As páginas 39 e 40 são do Questionário de Percepção.
    if pagina_num > 38:
        break

    texto = pagina.get_text()
    linhas = texto.splitlines()

    for linha in linhas:
        linha_limpa = linha.strip()

        correspondencia = padrao_questao.match(linha_limpa)

        if correspondencia:
            numero = int(correspondencia.group(1))

            if questao_atual is not None:
                questoes[questao_atual] = {
                    "numero": questao_atual,
                    "ano": 2023,
                    "curso": "Engenharia de Computação",
                    "tipo": "objetiva",
                    "pagina_inicio": pagina_inicio,
                    "texto": "\n".join(texto_atual).strip()
                }

            questao_atual = numero
            pagina_inicio = pagina_num
            texto_atual = []
            continue

        if questao_atual is not None:
            texto_atual.append(linha)

if questao_atual is not None:
    questoes[questao_atual] = {
        "numero": questao_atual,
        "ano": 2023,
        "curso": "Engenharia de Computação",
        "tipo": "objetiva",
        "pagina_inicio": pagina_inicio,
        "texto": "\n".join(texto_atual).strip()
    }

doc.close()

dados = [
    questoes[numero]
    for numero in sorted(questoes)
]

with open(OUTPUT_PATH, "w", encoding="utf-8") as arquivo:
    json.dump(dados, arquivo, ensure_ascii=False, indent=2)

print(f"JSON criado com sucesso: {OUTPUT_PATH}")
print(f"Total de questões salvas: {len(dados)}")
