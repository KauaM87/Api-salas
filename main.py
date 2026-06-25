import logging
import os
import shutil
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from services.ia import analisar_planta, get_device_info
from services.java_client import enviar_para_java
from services.formatador import formatar_estacoes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    device = get_device_info()
    logger.info("=== API Salas iniciada ===")
    logger.info("Dispositivo de inferência: %s", device)
    yield
    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)
        logger.info("Pasta de uploads temporários limpa.")


app = FastAPI(
    title="API Salas",
    description="API para análise e monitoramento de plantas baixas (salas empresariais) via IA.",
    version="1.3.0",
    lifespan=lifespan,
)


@app.get("/", summary="Health check")
def root():
    device = get_device_info()
    return {"status": "API rodando", "versao": "1.3.0", "dispositivo_ia": device}


@app.post(
    "/analisar",
    summary="Analisa planta baixa",
    response_description="Lista de estações detectadas com contagem de itens",
)
async def analisar(file: UploadFile = File(...)):
    """
    Recebe uma imagem (PNG, JPG, JPEG) de uma planta baixa,
    detecta os objetos com IA e retorna as estações agrupadas por mesa.

    Formato de retorno:
    ```json
    [
      {
        "estacao": 1,
        "coordx": 835,
        "coordy": 948,
        "itens": {
          "cadeira": 4,
          "monitor": 2,
          "mesa": 1
        }
      }
    ]
    ```
    """
    EXTENSOES_PERMITIDAS = (".png", ".jpg", ".jpeg")

    if not file.filename or not file.filename.lower().endswith(EXTENSOES_PERMITIDAS):
        raise HTTPException(
            status_code=400,
            detail=f"Formato inválido. Apenas imagens {', '.join(EXTENSOES_PERMITIDAS)} são aceitas.",
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
        logger.info("Iniciando análise de planta: %s", file.filename)

        # CORREÇÃO DO BUG: analisar_planta é async (usa ThreadPoolExecutor),
        # por isso DEVE ser chamada com await. Sem o await, Python retorna
        # um objeto coroutine em vez do dict — causando o erro
        # "argument of type 'coroutine' is not a container or iterable"
        resultado_bruto = await analisar_planta(caminho)

        if isinstance(resultado_bruto, dict) and "error" in resultado_bruto:
            raise HTTPException(status_code=422, detail=resultado_bruto["error"])

        estacoes = formatar_estacoes(resultado_bruto)
        logger.info("Análise concluída. %d estação(ões) detectada(s).", len(estacoes))

        # Envia para o Java — falha não bloqueia a resposta ao cliente
        try:
            resposta_java = await enviar_para_java(estacoes)
            if not resposta_java.get("sucesso"):
                logger.warning("Falha ao notificar API Java: %s", resposta_java.get("erro"))
        except Exception as e_java:
            logger.error("Exceção ao chamar enviar_para_java: %s", str(e_java))

        return estacoes

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro inesperado na análise da planta.")
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)
