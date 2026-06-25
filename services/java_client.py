import httpx
import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

logger = logging.getLogger(__name__)

JAVA_API_URL = os.getenv("JAVA_API_URL", "http://localhost:8080/salas/importar")


async def enviar_para_java(dados: List[Dict[str, Any]]) -> dict:
    """
    Envia o resultado da análise de IA para a API Java via POST.

    BUG CORRIGIDO: parâmetro era anotado como `dict` mas recebe uma `List`.
    Também adicionado logging dos erros para facilitar debugging em produção.

    Retorna:
      - {"sucesso": True, "status": <código HTTP>} em caso de sucesso
      - {"sucesso": False, "erro": <mensagem>} em caso de falha
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(JAVA_API_URL, json=dados, timeout=10.0)
            response.raise_for_status()
            logger.info("Dados enviados ao Java com sucesso. Status: %s", response.status_code)
            return {"sucesso": True, "status": response.status_code}
        except httpx.TimeoutException:
            msg = "Timeout: a API Java não respondeu a tempo."
            logger.warning(msg)
            return {"sucesso": False, "erro": msg}
        except httpx.ConnectError:
            msg = f"Não foi possível conectar à API Java em: {JAVA_API_URL}"
            logger.warning(msg)
            return {"sucesso": False, "erro": msg}
        except httpx.HTTPStatusError as e:
            msg = f"Erro HTTP {e.response.status_code}: {e.response.text}"
            logger.error(msg)
            return {"sucesso": False, "erro": msg}
        except httpx.HTTPError as e:
            msg = str(e)
            logger.error("Erro inesperado ao enviar para Java: %s", msg)
            return {"sucesso": False, "erro": msg}
