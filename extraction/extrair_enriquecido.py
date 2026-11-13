"""
Extrai e enriquece as questões do ENADE 2023 — Engenharia de Computação.

Campos gerados por documento:
  id, numero, numero_discursiva, ano, curso, area,
  secao (FG|CE), tipo_questao (objetiva|discursiva),
  gabarito, anulada, enunciado, alternativas,
  texto_completo, pdf_origem, pagina_inicio
"""

import fitz
import re
import json
import warnings

warnings.filterwarnings("ignore")

# Configurações 
BASE_DIR     = "c:/Users/cauad/OneDrive/Área de Trabalho/Conteúdos - Faculdade/BigData/TP2/TP2-BigData/extraction"
PDF_PROVA    = f"{BASE_DIR}/2023_PV_engenharia_da_computacao.pdf"
PDF_GABARITO = f"{BASE_DIR}/2023_GB_engenharia_da_computacao.pdf"
OUTPUT_PATH  = f"{BASE_DIR}/questoes_enriquecidas.json"

ANO   = 2023
CURSO = "Engenharia de Computação"
AREA  = "Engenharia de Computação"


# 1. Gabarito 
def extrair_gabarito(pdf_path):
    doc = fitz.open(pdf_path)
    gabarito = {}
    padrao_obj  = re.compile(r"QUESTÃO\s+(\d+)\s+([A-E]|ANULADA)")
    padrao_disc = re.compile(r"QUESTÃO DISCURSIVA\s+(\d+)\s+(\*{3}|ANULADA)")
    for page in doc:
        texto = page.get_text()
        for m in padrao_disc.finditer(texto):
            gabarito[f"DISCURSIVA_{m.group(1)}"] = m.group(2)
        for m in padrao_obj.finditer(texto):
            gabarito[int(m.group(1))] = m.group(2)
    doc.close()
    return gabarito


#  2. Limpeza 
CORRECOES = {
    "anti gos": "antigos", "multi dimensional": "multidimensional",
    "políti cas": "políticas", "confl itos": "conflitos",
    "geopolíti cos": "geopolíticos", "climáti cas": "climáticas",
    "justi fi cati va": "justificativa", "fi nal": "final",
    "di mensão": "dimensão", "di mensões": "dimensões",
    "econômi cas": "econômicas", "soci ológico": "sociológico",
    "htt ps": "https", "Safi dy": "Safidy",
    "objeti vas": "objetivas", "específi co": "específico",
    "signifi cati va": "significativa", "consti tui": "constitui",
    "desafi o": "desafio", "investi mentos": "investimentos",
    "infanti l": "infantil", "últi mos": "últimos",
    "prati camente": "praticamente", "dift eria": "difteria",
    "gráfi co": "gráfico", "parti cipação": "participação",
    "parti r": "partir", "ati ngiu": "atingiu",
    "disrupti va": "disruptiva", "drasti camente": "drasticamente",
    "ati vidades": "atividades", "repeti ti vas": "repetitivas",
    "esti mula": "estimula", "profi ssões": "profissões",
    "identi fi cação": "identificação", "diagnósti co": "diagnóstico",
    "maléfi cas": "maléficas",
}

def limpar_texto(texto):
    for errado, correto in CORRECOES.items():
        texto = texto.replace(errado, correto)
    linhas = [l.strip() for l in texto.splitlines()]
    filtradas = []
    i = 0
    while i < len(linhas):
        l = linhas[i]
        if "VALIDINEP" in l or "VALIDIN3P" in l:
            i += 1; continue
        if re.fullmatch(r"\*R\d+\*", l):
            i += 1; continue
        if (re.fullmatch(r"\d{1,2}", l)
                and i + 1 < len(linhas)
                and linhas[i + 1] == CURSO):
            i += 2; continue
        filtradas.append(l)
        i += 1
    result = []
    prev_empty = False
    for l in filtradas:
        if not l:
            if not prev_empty:
                result.append("")
            prev_empty = True
        else:
            result.append(l)
            prev_empty = False
    return "\n".join(result).strip()


# 3. Extração de alternativas A–E 

ANCORAS_ALTERNATIVAS = re.compile(
    r"(assinale|é correto|são corretas|são verdadeiras|"
    r"opção correta|opção que|afirma em|afirmações|asserções|"
    r"da ordem de|correto afirmar|correto concluir|marque a|"
    r"incorreto afirmar|verdadeiro afirmar|pode-se afirmar)",
    re.IGNORECASE,
)


LINHA_ALT = re.compile(r"^([A-E])[\s\t]{1,4}(.+)$")

SEQUENCIA_ESPERADA = {"A": "B", "B": "C", "C": "D", "D": "E"}


def extrair_alternativas(texto_limpo):
    linhas = texto_limpo.splitlines()

    def coletar_a_partir(idx_a):
        """Coleta alternativas a partir do índice da linha 'A', exigindo sequência."""
        alts = []
        proxima = "A"
        alt_letra = None
        alt_texto = []
        for linha in linhas[idx_a:]:
            m = LINHA_ALT.match(linha)
            if m and m.group(1) == proxima:
                if alt_letra:
                    alts.append({"letra": alt_letra, "texto": " ".join(alt_texto).strip()})
                alt_letra = m.group(1)
                alt_texto = [m.group(2).strip()]
                proxima = SEQUENCIA_ESPERADA.get(alt_letra, "DONE")
            elif m and alt_letra and m.group(1) != proxima:
                if alt_letra:
                    alt_texto.append(linha.strip())
            elif alt_letra and linha.strip():
                alt_texto.append(linha.strip())
        if alt_letra:
            alts.append({"letra": alt_letra, "texto": " ".join(alt_texto).strip()})
        return alts

    idx_inicio_alts = None
    for i, l in enumerate(linhas):
        if ANCORAS_ALTERNATIVAS.search(l):
            for j in range(i + 1, min(i + 7, len(linhas))):
                m = LINHA_ALT.match(linhas[j])
                if m and m.group(1) == "A":
                    idx_inicio_alts = j
                    break
            if idx_inicio_alts is not None:
                break

    
    if idx_inicio_alts is None:
        for i in range(len(linhas) - 1):
            m1 = LINHA_ALT.match(linhas[i])
            m2 = LINHA_ALT.match(linhas[i + 1]) if i + 1 < len(linhas) else None
            if m1 and m1.group(1) == "A" and m2 and m2.group(1) == "B":
                idx_inicio_alts = i
                break

    if idx_inicio_alts is None:
        return texto_limpo, []

    enunciado = "\n".join(linhas[:idx_inicio_alts]).strip()
    alternativas = coletar_a_partir(idx_inicio_alts)
    return enunciado, alternativas


# 4. Extração das questões do PDF 
def extrair_questoes(pdf_path):
    doc = fitz.open(pdf_path)
    questoes = {}
    questao_atual_id = None
    texto_atual = []
    pagina_inicio = None
    secao_atual = "FG"

    padrao_obj  = re.compile(r"^QUESTÃO\s+0?(\d{1,2})\s*$")
    padrao_disc = re.compile(r"^QUESTÃO DISCURSIVA\s+0?(\d+)\s*$")
    padrao_fg   = re.compile(r"FORMAÇÃO GERAL")
    padrao_ce   = re.compile(r"COMPONENTE ESPECÍF")

    for pagina_num, pagina in enumerate(doc, start=1):
        if pagina_num > 38:
            break
        linhas = pagina.get_text().splitlines()
        for linha in linhas:
            lc = linha.strip()
            if padrao_fg.search(lc):
                secao_atual = "FG"
            if padrao_ce.search(lc):
                secao_atual = "CE"

            m_disc = padrao_disc.match(lc)
            if m_disc:
                if questao_atual_id is not None:
                    questoes[questao_atual_id]["texto"] = "\n".join(texto_atual).strip()
                num = int(m_disc.group(1))
                chave = f"DISCURSIVA_{num}"
                questao_atual_id = chave
                texto_atual = []
                pagina_inicio = pagina_num
                questoes[chave] = {
                    "numero": None,
                    "numero_discursiva": num,
                    "secao": secao_atual,
                    "tipo_questao": "discursiva",
                    "pagina_inicio": pagina_num,
                }
                continue

            m_obj = padrao_obj.match(lc)
            if m_obj:
                if questao_atual_id is not None:
                    questoes[questao_atual_id]["texto"] = "\n".join(texto_atual).strip()
                num = int(m_obj.group(1))
                questao_atual_id = num
                texto_atual = []
                pagina_inicio = pagina_num
                questoes[num] = {
                    "numero": num,
                    "numero_discursiva": None,
                    "secao": secao_atual,
                    "tipo_questao": "objetiva",
                    "pagina_inicio": pagina_num,
                }
                continue

            if questao_atual_id is not None:
                texto_atual.append(linha)

    if questao_atual_id is not None:
        questoes[questao_atual_id]["texto"] = "\n".join(texto_atual).strip()

    doc.close()
    return questoes


# 5. Montar documentos finais 
def montar_documentos(questoes, gabarito):
    documentos = []

    chaves = sorted(questoes.keys(), key=lambda k: (isinstance(k, int), k if isinstance(k, int) else int(k.split("_")[1])))

    for chave in chaves:
        q = questoes[chave]
        texto_bruto = q.get("texto", "")
        texto_limpo = limpar_texto(texto_bruto)

        gab = gabarito.get(chave) if isinstance(chave, int) else gabarito.get(str(chave), gabarito.get(chave, "***"))
        anulada = (gab == "ANULADA")

        if q["tipo_questao"] == "objetiva":
            enunciado, alternativas = extrair_alternativas(texto_limpo)
        else:
            enunciado = texto_limpo
            alternativas = []

        doc_id = f"{ANO}-{CURSO.replace(' ', '_')}-{chave}"

        documentos.append({
            "id": doc_id,
            "numero": q["numero"],
            "numero_discursiva": q.get("numero_discursiva"),
            "ano": ANO,
            "curso": CURSO,
            "area": AREA,
            "secao": q["secao"],
            "tipo_questao": q["tipo_questao"],
            "gabarito": gab,
            "anulada": anulada,
            "enunciado": enunciado,
            "alternativas": alternativas,
            "texto_completo": texto_limpo,
            "pdf_origem": PDF_PROVA.split("/")[-1],
            "pagina_inicio": q["pagina_inicio"],
        })

    return documentos


# Execução
if __name__ == "__main__":
    print("1. Extraindo gabarito...")
    gabarito = extrair_gabarito(PDF_GABARITO)
    print(f"   {len(gabarito)} entradas no gabarito")

    print("2. Extraindo questões...")
    questoes = extrair_questoes(PDF_PROVA)
    print(f"   {len(questoes)} questões encontradas")

    print("3. Montando documentos...")
    documentos = montar_documentos(questoes, gabarito)

    obj_fg   = [d for d in documentos if d["tipo_questao"] == "objetiva"   and d["secao"] == "FG"]
    obj_ce   = [d for d in documentos if d["tipo_questao"] == "objetiva"   and d["secao"] == "CE"]
    disc_fg  = [d for d in documentos if d["tipo_questao"] == "discursiva" and d["secao"] == "FG"]
    disc_ce  = [d for d in documentos if d["tipo_questao"] == "discursiva" and d["secao"] == "CE"]
    anuladas = [d for d in documentos if d["anulada"]]

    print(f"   FG objetivas   : {len(obj_fg)}")
    print(f"   FG discursivas : {len(disc_fg)}")
    print(f"   CE objetivas   : {len(obj_ce)}")
    print(f"   CE discursivas : {len(disc_ce)}")
    print(f"   Anuladas       : {len(anuladas)}")
    print(f"   TOTAL          : {len(documentos)}")

    # Verificação de alternativas
    print("\n4. Verificando alternativas extraídas...")
    for d in obj_fg + obj_ce:
        n_alts = len(d["alternativas"])
        status = "OK" if n_alts == 5 else f"ATENÇÃO ({n_alts} alts)"
        num = d["numero"]
        print(f"   Q{num:02d} [{d['secao']}] gabarito={d['gabarito']} alternativas={n_alts} → {status}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(documentos, f, ensure_ascii=False, indent=2)
    print(f"\n5. Salvo em: {OUTPUT_PATH}")

    # Exemplo de documento completo 
    q1 = next(d for d in documentos if d["numero"] == 1)
    print("\n=== EXEMPLO — Questão 01 ===")
    q1_preview = dict(q1)
    q1_preview["enunciado"] = q1_preview["enunciado"][:300] + "..." if len(q1_preview["enunciado"]) > 300 else q1_preview["enunciado"]
    q1_preview["texto_completo"] = "[omitido para brevidade]"
    print(json.dumps(q1_preview, ensure_ascii=False, indent=2))
