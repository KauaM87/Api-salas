"""
Transforma o resultado bruto da IA (lista de itens com polígonos)
no formato de estações agrupadas por mesa.

Saída esperada:
[
  {
    "estacao": 1,
    "coordx": 835,
    "coordy": 948,
    "itens": {
      "cadeira": 4,
      "Monitor": 2
    }
  },
  ...
]

Lógica:
- Cada "mesa" detectada vira uma estação.
- O centroide da mesa define as coordenadas (coordx, coordy).
- Itens próximos à mesa (dentro da margem) são agrupados e contados.
"""

from typing import List, Dict, Any


def _centroide(poligono: List[List[float]]) -> tuple:
    xs = [p[0] for p in poligono]
    ys = [p[1] for p in poligono]
    return round(sum(xs) / len(xs)), round(sum(ys) / len(ys))


def _bbox(poligono: List[List[float]]) -> tuple:
    xs = [p[0] for p in poligono]
    ys = [p[1] for p in poligono]
    return min(xs), min(ys), max(xs), max(ys)


def _item_pertence_mesa(
    item_poligono: List[List[float]],
    mesa_poligono: List[List[float]],
    margem: int = 300
) -> bool:
    """Verifica se um item está próximo o suficiente de uma mesa."""
    ix1, iy1, ix2, iy2 = _bbox(item_poligono)
    mx1, my1, mx2, my2 = _bbox(mesa_poligono)
    return not (
        ix2 < mx1 - margem or
        ix1 > mx2 + margem or
        iy2 < my1 - margem or
        iy1 > my2 + margem
    )


def formatar_estacoes(resultado_ia: Dict[str, Any], margem: int = 300) -> List[Dict]:
    """
    Converte o resultado da IA no formato de estações.

    Args:
        resultado_ia: dict com chave "itens" (lista de objetos detectados)
        margem: distância em pixels para associar um item a uma mesa

    Returns:
        Lista de estações no formato { estacao, coordx, coordy, itens }
    """
    todos_itens = resultado_ia.get("itens", [])

    mesas = [item for item in todos_itens if item["nome"].lower() == "mesa"]
    outros = [item for item in todos_itens if item["nome"].lower() != "mesa"]

    estacoes = []
    for idx, mesa in enumerate(mesas, start=1):
        cx, cy = _centroide(mesa["poligono"])

        contagem: Dict[str, int] = {}
        for item in outros:
            if _item_pertence_mesa(item["poligono"], mesa["poligono"], margem):
                nome = item["nome"]
                contagem[nome] = contagem.get(nome, 0) + 1

        estacoes.append({
            "estacao": idx,
            "coordx": cx,
            "coordy": cy,
            "itens": contagem
        })

    return estacoes
