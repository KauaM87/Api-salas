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
    fator_raio: float = 1.8,  # Reduzido de 2.5 para não expandir demais nas pontas
    raio_min: int = 150,     # Ajustado para cobrir cadeiras coladas
    raio_max: int = 350,     # Reduzido drasticamente de 700 para evitar roubo de objetos distantes
) -> List[Dict]:
    todos_itens = resultado_ia.get("itens", [])
    if not todos_itens:
        return []

    # Classes que NUNCA devem entrar em agrupamentos de mesas
    ITENS_INFRAESTRUTURA = ["painel led", "tv", "impressora"]

    # 1. Separar o que é mesa legítima e o que é elemento isolado de infraestrutura
    mesas_brutas = [it for it in todos_itens if it["nome"].lower() == "mesa"]
    itens_infra = [it for it in todos_itens if it["nome"].lower() in ITENS_INFRAESTRUTURA]
    
    # Itens móveis/periféricos que vão tentar se agrupar às mesas
    itens_para_agrupar = [
        it for it in todos_itens 
        if it["nome"].lower() not in ITENS_INFRAESTRUTURA and it["nome"].lower() != "mesa"
    ]

    # 2. Filtrar e definir centros das mesas
    mesas: List[Dict] = []
    for m in mesas_brutas:
        cx, cy = _centroide(m["poligono"])
        if any(_distancia(cx, cy, ms["cx"], ms["cy"]) < margem_fusao for ms in mesas):
            continue
        diag = _diagonal_bbox(m["poligono"])
        mesas.append({"cx": cx, "cy": cy, "diagonal": diag})

    # Caso não ache mesas, trata tudo que sobrou como uma estação genérica
    if not mesas and not itens_infra:
        contagem: Dict[str, int] = {}
        for it in todos_itens:
            nome = it["nome"].lower()
            contagem[nome] = contagem.get(nome, 0) + 1
        return [{"estacao": 1, "coordx": 0, "coordy": 0, "itens": contagem}]

    estacoes: List[Dict] = []
    id_atual = 1

    # 3. Inicializar as estações baseadas em mesas com a própria mesa já contabilizada
    for ms in mesas:
        raio = max(raio_min, min(raio_max, ms["diagonal"] * fator_raio))
        estacoes.append({
            "estacao": id_atual,
            "coordx": round(ms["cx"]),
            "coordy": round(ms["cy"]),
            "_raio": raio,
            "itens": {"mesa": 1},  # A própria mesa já começa contando aqui
        })
        id_atual += 1

    # 4. Distribuir cadeiras, monitores, etc., para a mesa mais próxima dentro do raio seguro
    for item in itens_para_agrupar:
        cx_it, cy_it = _centroide(item["poligono"])
        nome = item["nome"].lower()

        melhor_idx = None
        melhor_dist = float("inf")

        for i, est in enumerate(estacoes):
            dist = _distancia(cx_it, cy_it, est["coordx"], est["coordy"])
            # Penaliza severamente se o objeto estiver fora do raio limite daquela mesa
            peso = dist if dist <= est["_raio"] else dist * 3.0
            if peso < melhor_dist:
                melhor_dist = peso
                melhor_idx = i

        if melhor_idx is not None:
            itens = estacoes[melhor_idx]["itens"]
            itens[nome] = itens.get(nome, 0) + 1

    # Limpa a propriedade temporária de raio
    for est in estacoes:
        est.pop("_raio", None)

    # 5. Adicionar os itens de infraestrutura como blocos/estações totalmente independentes
    for infra in itens_infra:
        cx_inf, cy_inf = _centroide(infra["poligono"])
        nome_inf = infra["nome"].lower()
        
        estacoes.append({
            "estacao": id_atual,
            "coordx": round(cx_inf),
            "coordy": round(cy_inf),
            "itens": {nome_inf: 1}
        })
        id_atual += 1

    return estacoes