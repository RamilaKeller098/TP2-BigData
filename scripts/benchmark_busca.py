#!/usr/bin/env python3
"""Benchmark da busca ENADE HUB (latência p50/p95/p99, vazão e taxa de acerto do cache).

Usa só a biblioteca padrão. Roda dentro da rede do Docker Compose (veja o README / docs).
Fases:
  1. frio  : consultas únicas (cache miss, passa pelo Elasticsearch)
  2. quente: repete as mesmas consultas (cache hit, responde pelo Redis)
  3. misto : carga realista, poucas consultas muito repetidas e outras raras
"""
import argparse
import json
import math
import random
import statistics
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

TERMOS = [
    "algoritmo", "grafo", "rota", "banco de dados", "software", "rede",
    "segurança", "sistema", "dados", "engenharia", "computação", "lógica",
    "complexidade", "arquitetura", "processo", "teste", "ética", "memória",
    "protocolo", "linguagem",
]
TIPOS = [None, "objetiva", "discursiva"]
SECOES = [None, "CE", "FG"]


def consultas_unicas(n, semente=7):
    """Gera n consultas com chaves de cache distintas (variando termo, tipo, seção, página e tamanho)."""
    rnd = random.Random(semente)
    vistas, saida = set(), []
    while len(saida) < n:
        params = {"size": rnd.choice([5, 10, 15, 20, 25, 30, 40, 50]), "page": rnd.choice([1, 1, 1, 2])}
        if rnd.random() < 0.85:
            params["q"] = rnd.choice(TERMOS)
        tipo, secao = rnd.choice(TIPOS), rnd.choice(SECOES)
        if tipo:
            params["tipo_questao"] = tipo
        if secao:
            params["secao"] = secao
        chave = tuple(sorted(params.items()))
        if chave not in vistas:
            vistas.add(chave)
            saida.append(params)
    return saida


def requisitar(base, params):
    url = f"{base}/api/v1/questoes/busca?{urllib.parse.urlencode(params)}"
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            corpo = json.loads(resp.read())
            ok, hit = resp.status == 200, bool(corpo.get("cache_hit"))
    except Exception:
        ok, hit = False, False
    return (time.perf_counter() - inicio) * 1000.0, ok, hit


def percentil(valores_ordenados, p):
    if not valores_ordenados:
        return float("nan")
    k = max(0, min(len(valores_ordenados) - 1, math.ceil(p / 100.0 * len(valores_ordenados)) - 1))
    return valores_ordenados[k]


def executar(nome, base, lista, concorrencia):
    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concorrencia) as pool:
        resultados = list(pool.map(lambda p: requisitar(base, p), lista))
    duracao = time.perf_counter() - inicio
    lat = sorted(r[0] for r in resultados if r[1])
    erros = sum(1 for r in resultados if not r[1])
    hits = sum(1 for r in resultados if r[1] and r[2])
    ok = len(resultados) - erros
    resumo = {
        "fase": nome,
        "requisicoes": len(resultados),
        "erros": erros,
        "concorrencia": concorrencia,
        "vazao_req_s": round(len(resultados) / duracao, 1),
        "latencia_ms": {
            "min": round(lat[0], 2) if lat else None,
            "media": round(statistics.mean(lat), 2) if lat else None,
            "p50": round(percentil(lat, 50), 2),
            "p95": round(percentil(lat, 95), 2),
            "p99": round(percentil(lat, 99), 2),
            "max": round(lat[-1], 2) if lat else None,
        },
        "cache_hit_pct": round(100.0 * hits / ok, 1) if ok else None,
    }
    l = resumo["latencia_ms"]
    print(f"[{nome:7}] n={resumo['requisicoes']:4} erros={erros} c={concorrencia:2} "
          f"{resumo['vazao_req_s']:7.1f} req/s | p50={l['p50']}ms p95={l['p95']}ms p99={l['p99']}ms "
          f"| cache_hit={resumo['cache_hit_pct']}%")
    return resumo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://api:8000")
    ap.add_argument("--frio", type=int, default=100, help="consultas únicas na fase fria")
    ap.add_argument("--quente", type=int, default=500)
    ap.add_argument("--misto", type=int, default=1000)
    ap.add_argument("--concorrencia", type=int, default=10)
    ap.add_argument("--saida", default="/scripts/resultados_busca.json")
    a = ap.parse_args()

    # Garante consultas inéditas a cada execução (o cache do Redis dura CACHE_TTL_SECONDS).
    semente = int(time.time()) % 100000
    unicas = consultas_unicas(a.frio + 20, semente)
    frias, populares = unicas[: a.frio], unicas[a.frio:]
    rnd = random.Random(semente)

    print(f"Alvo: {a.base} | semente={semente}")
    resumo = [executar("frio", a.base, frias, min(5, a.concorrencia))]
    quentes = [rnd.choice(frias) for _ in range(a.quente)]
    resumo.append(executar("quente", a.base, quentes, a.concorrencia))
    # misto: 80% das requisições nas 20 consultas "populares", 20% em consultas novas e raras
    raras = consultas_unicas(a.misto, semente + 1)
    mistas = [rnd.choice(populares) if rnd.random() < 0.8 else rnd.choice(raras) for _ in range(a.misto)]
    resumo.append(executar("misto", a.base, mistas, a.concorrencia))

    try:
        with open(a.saida, "w", encoding="utf-8") as f:
            json.dump(resumo, f, ensure_ascii=False, indent=2)
        print(f"Resultados salvos em {a.saida}")
    except OSError as e:
        print(f"(não foi possível salvar o JSON: {e})")


if __name__ == "__main__":
    main()
