from ultralytics import YOLO
import cv2
import os

MODEL_PATH = "best.pt"

# Carrega o modelo uma única vez ao iniciar o módulo (evita recarregar a cada requisição)
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Modelo YOLO não encontrado em '{MODEL_PATH}'. "
        "Certifique-se de que o arquivo 'best.pt' está na raiz do projeto."
    )

model = YOLO(MODEL_PATH)


def analisar_planta(caminho_imagem: str) -> dict:
    """
    Analisa uma imagem de planta baixa usando o modelo YOLO customizado.
    
    Retorna um dicionário com:
      - itens: lista de objetos detectados (nome, tipo, quantidade, confiança, polígono)
      - total_itens: número total de detecções
      - observacoes_gerais: resumo textual
    """
    img = cv2.imread(caminho_imagem)

    if img is None:
        return {"error": f"Não foi possível ler a imagem no caminho: {caminho_imagem}"}

    # Inferência com threshold de confiança 0.15
    results = model(img, conf=0.15)

    itens_detectados = []

    for r in results:
        if r.masks is None:
            continue

        classes = r.boxes.cls.cpu().numpy()
        confidencias = r.boxes.conf.cpu().numpy()
        poligonos = r.masks.xy  # Lista de arrays numpy com pontos do polígono

        for i, poligono in enumerate(poligonos):
            class_id = int(classes[i])
            label = model.names[class_id]
            conf = float(confidencias[i])

            item = {
                "nome": label,
                "tipo": label,
                "quantidade": 1,
                "observacoes": f"Confiança: {conf:.2f}",
                "poligono": poligono.tolist()
            }
            itens_detectados.append(item)

    total = len(itens_detectados)

    return {
        "itens": itens_detectados,
        "total_itens": total,
        "observacoes_gerais": f"A IA detectou um total de {total} objeto(s) na imagem."
    }
