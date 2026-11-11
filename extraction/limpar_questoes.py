import json
import re

INPUT_PATH = "extraction/questoes_extraidas.json"
OUTPUT_PATH = "extraction/questoes_limpa.json"


def limpar_texto(texto):
    # Corrige quebras de palavras causadas pela extração do PDF.
    correcoes = {
        "anti gos": "antigos",
        "multi dimensional": "multidimensional",
        "políti cas": "políticas",
        "confl itos": "conflitos",
        "geopolíti cos": "geopolíticos",
        "climáti cas": "climáticas",
        "justi fi cati va": "justificativa",
        "fi nal": "final",
        "di mensão": "dimensão",
        "di mensões": "dimensões",
        "econômi cas": "econômicas",
        "soci ológico": "sociológico",
        "soci ológicas": "sociológicas",
        "catástrofes": "catástrofes",
        "htt ps": "https",
        "Safi dy": "Safidy",
    }

    for errado, correto in correcoes.items():
        texto = texto.replace(errado, correto)

    # Remove espaços desnecessários no início/fim das linhas.
    linhas = [linha.strip() for linha in texto.splitlines()]

    # Remove marcas de validação, códigos e rodapés do PDF.
    linhas_filtradas = []
    i = 0

    while i < len(linhas):
        linha = linhas[i]

        # Remove marcas de fundo do PDF.
        if "VALIDINEP" in linha or "VALIDIN3P" in linha:
            i += 1
            continue

        # Remove códigos de identificação isolados.
        if re.fullmatch(r"\*R\d+\*", linha):
            i += 1
            continue

        # Remove número da página seguido do nome do curso.
        if (
            re.fullmatch(r"\d{1,2}", linha)
            and i + 1 < len(linhas)
            and linhas[i + 1] == "Engenharia de Computação"
        ):
            i += 2
            continue

        linhas_filtradas.append(linha)
        i += 1

    linhas = linhas_filtradas

    # Remove linhas vazias repetidas.
    linhas_limpa = []
    linha_anterior_vazia = False

    for linha in linhas:
        if not linha:
            if not linha_anterior_vazia:
                linhas_limpa.append("")
            linha_anterior_vazia = True
        else:
            linhas_limpa.append(linha)
            linha_anterior_vazia = False

    texto = "\n".join(linhas_limpa).strip()

    return texto


with open(INPUT_PATH, "r", encoding="utf-8") as arquivo:
    questoes = json.load(arquivo)

for questao in questoes:
    questao["texto"] = limpar_texto(questao["texto"])

with open(OUTPUT_PATH, "w", encoding="utf-8") as arquivo:
    json.dump(questoes, arquivo, ensure_ascii=False, indent=2)

print(f"Arquivo criado com sucesso: {OUTPUT_PATH}")
print(f"Total de questões processadas: {len(questoes)}")
