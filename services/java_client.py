import httpx
import os
from dotenv import load_dotenv

load_dotenv()

JAVA_API_URL = os.getenv("JAVA_API_URL", "http://localhost:8080/salas/importar")


async def enviar_para_java(dados: dict) -> dict:
    """
    Envia o resultado da análise de IA para a API Java via POST.
    
    Retorna:
      - {"sucesso": True, "status": <código HTTP>} em caso de sucesso
      - {"sucesso": False, "erro": <mensagem>} em caso de falha
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(JAVA_API_URL, json=dados, timeout=10.0)
            response.raise_for_status()
            return {"sucesso": True, "status": response.status_code}
        except httpx.TimeoutException:
            return {"sucesso": False, "erro": "Timeout: a API Java não respondeu a tempo."}
        except httpx.ConnectError:
            return {"sucesso": False, "erro": f"Não foi possível conectar à API Java em: {JAVA_API_URL}"}
        except httpx.HTTPStatusError as e:
            return {"sucesso": False, "erro": f"Erro HTTP {e.response.status_code}: {e.response.text}"}
        except httpx.HTTPError as e:
            return {"sucesso": False, "erro": str(e)}
