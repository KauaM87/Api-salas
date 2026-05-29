import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

import cv2
import torch
from ultralytics import YOLO

MODEL_PATH = os.getenv("MODEL_PATH", "best.pt")
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.15"))

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Modelo YOLO não encontrado em '{MODEL_PATH}'. "
        "Certifique-se de que o arquivo 'best.pt' está na raiz do projeto."
    )

# Detecta automaticamente GPU (CUDA) ou CPU
_device = "cuda" if torch.cuda.is_available() else "cpu"

# Carrega o modelo uma única vez ao iniciar (evita recarregar a cada requisição)
model = YOLO(MODEL_PATH)
model.to(_device)

# Executor para rodar inferência YOLO sem bloquear o event loop do FastAPI
_executor = ThreadPoolExecutor(max_workers=2)


def get_device_info() -> str:
    """Retorna uma string descritiva do dispositivo usado para inferência."""
    if _device == "cuda":
        nome_gpu = torch.cuda.get_device_name(0)
        return f"GPU — {nome_gpu}"
    return "CPU"


def _inferir(caminho_imagem: str) -> dict:
    """
    Executa a inferência YOLO de forma síncrona (chamado via executor).
    Separa a lógica de I/O da inferência para não bloquear o event loop.
    """
    img = cv2.imread(caminho_imagem)
    if img is None:
        return {"error": f"Não foi possível ler a imagem: {caminho_imagem}"}

    results = model(img, conf=CONF_THRESHOLD, device=_device, verbose=False)
    itens_detectados = []

    for r in results:
        boxes = r.boxes
        if boxes is None or len(boxes) == 0:
            continue

        classes = boxes.cls.cpu().numpy()
        confidencias = boxes.conf.cpu().numpy()
        xyxy = boxes.xyxy.cpu().numpy()
        poligonos_seg = r.masks.xy if r.masks is not None else None

        for i in range(len(classes)):
            class_id = int(classes[i])
            label = model.names[class_id].lower()
            conf = float(confidencias[i])

            if poligonos_seg is not None and i < len(poligonos_seg):
                poligono = poligonos_seg[i].tolist()
            else:
                x1, y1, x2, y2 = xyxy[i]
                poligono = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

            itens_detectados.append({
                "nome": label,
                "tipo": label,
                "quantidade": 1,
                "observacoes": f"Confiança: {conf:.2f}",
                "poligono": poligono,
            })

    total = len(itens_detectados)
    return {
        "itens": itens_detectados,
        "total_itens": total,
        "observacoes_gerais": f"A IA detectou um total de {total} objeto(s) na imagem.",
    }


async def analisar_planta(caminho_imagem: str) -> dict:
    """
    Analisa uma imagem de planta baixa usando o modelo YOLO customizado.
    A inferência roda em um ThreadPoolExecutor para não bloquear o event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _inferir, caminho_imagem)
