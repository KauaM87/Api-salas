from fastapi import FastAPI, UploadFile, File, HTTPException
from services.ia import analisar_planta
from services.java_client import enviar_para_java
from services.formatador import formatar_estacoes
import shutil
import os
import uuid

app = FastAPI(
    title="API Salas",
    description="API para análise e monitoramento de plantas baixas (salas empresariais) via IA.",
    version="1.0.0"
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def root():
    return {"status": "API rodando", "versao": "1.0.0"}


@app.post("/analisar")
async def analisar(file: UploadFile = File(...)):
    """
    Recebe uma imagem (PNG, JPG, JPEG) de uma planta baixa,
    detecta os objetos com IA e retorna as estações agrupadas por mesa.

    Formato de retorno:
    [
      {
        "estacao": 1,
        "coordx": 835,
        "coordy": 948,
        "itens": {
          "cadeira": 4,
          "Monitor": 2
        }
      }
    ]
    """
    EXTENSOES_PERMITIDAS = (".png", ".jpg", ".jpeg")

    if not file.filename.lower().endswith(EXTENSOES_PERMITIDAS):
        raise HTTPException(
            status_code=400,
            detail=f"Formato inválido. Apenas imagens {', '.join(EXTENSOES_PERMITIDAS)} são aceitas."
        )

    extensao = os.path.splitext(file.filename)[1].lower()
    nome_unico = f"{uuid.uuid4().hex}{extensao}"
    caminho = os.path.join(UPLOAD_DIR, nome_unico)

    try:
        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")

    try:
        resultado_bruto = analisar_planta(caminho)

        if "error" in resultado_bruto:
            raise HTTPException(status_code=422, detail=resultado_bruto["error"])

        # Converte para o formato de estações agrupadas por mesa
        estacoes = formatar_estacoes(resultado_bruto)

        # Envia o resultado formatado para a API Java
        resposta_java = await enviar_para_java(estacoes)

        return estacoes

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)
