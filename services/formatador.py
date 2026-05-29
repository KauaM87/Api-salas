import math
from typing import List, Dict, Any, Tuple


def _centroide(poligono: List[List[float]]) -> Tuple[float, float]:
    xs = [p[0] for p in poligono]
    ys = [p[1] for p in poligono]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _diagonal_bbox(poligono: List[List[float]]) -> float:
    xs = [p[0] for p in poligono]
    ys = [p[1] for p in poligono]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    return math.sqrt(w * w + h * h)


def _distancia(ax, ay, bx, by) -> float:
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def formatar_estacoes(
    resultado_ia: Dict[str, Any],
    margem_fusao: int = 80,
    fator_raio: float = 2.5,
    raio_min: int = 180,
    raio_max: int = 700,
) -> List[Dict]:
    todos_itens = resultado_ia.get("itens", [])
    if not todos_itens:
        return []

    mesas_brutas = [it for it in todos_itens if it["nome"].lower() == "mesa"]

    mesas: List[Dict] = []
    for m in mesas_brutas:
        cx, cy = _centroide(m["poligono"])
        if any(_distancia(cx, cy, ms["cx"], ms["cy"]) < margem_fusao for ms in mesas):
            continue
        diag = _diagonal_bbox(m["poligono"])
        mesas.append({"cx": cx, "cy": cy, "diagonal": diag})

    if not mesas:
        contagem: Dict[str, int] = {}
        for it in todos_itens:
            nome = it["nome"].lower()
            contagem[nome] = contagem.get(nome, 0) + 1
        return [{"estacao": 1, "coordx": 0, "coordy": 0, "itens": contagem}]

    estacoes: List[Dict] = []
    for idx, ms in enumerate(mesas, start=1):
        raio = max(raio_min, min(raio_max, ms["diagonal"] * fator_raio))
        estacoes.append({
            "estacao": idx,
            "coordx": round(ms["cx"]),
            "coordy": round(ms["cy"]),
            "_raio": raio,
            "itens": {},
        })

    for item in todos_itens:
        cx_it, cy_it = _centroide(item["poligono"])
        nome = item["nome"].lower()

        melhor_idx = None
        melhor_dist = float("inf")

        for i, est in enumerate(estacoes):
            dist = _distancia(cx_it, cy_it, est["coordx"], est["coordy"])
            peso = dist if dist <= est["_raio"] else dist * 1.5
            if peso < melhor_dist:
                melhor_dist = peso
                melhor_idx = i

        if melhor_idx is not None:
            itens = estacoes[melhor_idx]["itens"]
            itens[nome] = itens.get(nome, 0) + 1

    resultado = []
    for est in estacoes:
        est.pop("_raio", None)
        resultado.append(est)

    return resultado