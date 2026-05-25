from pydantic import BaseModel
from typing import List, Optional


class Item(BaseModel):
    nome: str
    tipo: str
    quantidade: int
    observacoes: Optional[str] = None
    poligono: Optional[List[List[float]]] = None


class Sala_Empresarial(BaseModel):
    itens: List[Item]
    total_itens: int
    observacoes_gerais: Optional[str] = None
