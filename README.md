# API Salas 🏢

API Python para **monitoramento e análise de plantas baixas (salas empresariais)** usando um modelo YOLO customizado (segmentação de instâncias).

---

## ⚙️ Como funciona

1. O cliente envia uma imagem de planta baixa (PNG/JPG) via `POST /analisar`
2. A API salva temporariamente a imagem e aciona o modelo de IA (`best.pt`)
3. O modelo detecta e segmenta os objetos/itens presentes na planta
4. O resultado é enviado automaticamente para a API Java configurada
5. A API retorna a análise completa + resposta da API Java

---

## 🚀 Como rodar

### 1. Pré-requisitos

- Python 3.10+
- Arquivo `best.pt` na raiz do projeto (modelo YOLO treinado)

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`:

```bash
cp .env.example .env
```

Edite o `.env` com a URL da sua API Java:

```env
JAVA_API_URL=http://localhost:8080/salas/importar
```

### 4. Iniciar o servidor

```bash
uvicorn main:app --reload
```

A API estará disponível em: `http://localhost:8000`

---

## 📡 Endpoints

### `GET /`
Verifica se a API está no ar.

**Resposta:**
```json
{"status": "API rodando", "versao": "1.0.0"}
```

---

### `POST /analisar`
Analisa uma imagem de planta baixa.

**Body:** `multipart/form-data`
- `file` — imagem (`.png`, `.jpg` ou `.jpeg`)

**Resposta de sucesso:**
```json
{
  "analise": {
    "itens": [
      {
        "nome": "cadeira",
        "tipo": "cadeira",
        "quantidade": 1,
        "observacoes": "Confiança: 0.87",
        "poligono": [[x1, y1], [x2, y2], ...]
      }
    ],
    "total_itens": 3,
    "observacoes_gerais": "A IA detectou um total de 3 objeto(s) na imagem."
  },
  "java": {
    "sucesso": true,
    "status": 200
  }
}
```

**Erros possíveis:**
| Código | Motivo |
|--------|--------|
| 400 | Formato de arquivo inválido |
| 422 | Imagem não pôde ser processada |
| 500 | Erro interno na análise |

---

## 🗂️ Estrutura do projeto

```
Api-salas-main/
├── main.py                  # Entrypoint FastAPI
├── models.py                # Modelos Pydantic
├── requirements.txt         # Dependências
├── best.pt                  # Modelo YOLO (não incluído no git)
├── .env                     # Variáveis de ambiente (não incluído no git)
├── .env.example             # Exemplo de configuração
└── services/
    ├── ia.py                # Lógica de inferência YOLO
    └── java_client.py       # Cliente HTTP para a API Java
```

---

## 🔍 Documentação interativa

Com o servidor rodando, acesse:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
