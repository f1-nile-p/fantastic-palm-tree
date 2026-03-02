# PO Processing Pipeline

A self-hostable, AI-powered Purchase Order processing pipeline. Upload PO documents (PDF, DOCX, TXT), automatically extract structured data using a local LLM (Ollama), match line items against your master catalogue with vector search (Qdrant), review and approve orders in a web UI, then export ERP-ready XML — all running locally with Docker.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser                                                        │
│  React + Vite + Tailwind (port 3000)                            │
│    OrderQueue │ OrderDetail │ MasterData                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │ /api  (nginx proxy)
┌──────────────────────▼──────────────────────────────────────────┐
│  FastAPI Backend (port 8000)                                    │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐              │
│  │ /orders    │  │/master-data│  │  /export     │              │
│  └─────┬──────┘  └─────┬──────┘  └──────────────┘              │
│        │               │                                        │
│  ┌─────▼──────┐  ┌─────▼──────┐  ┌────────────────────────┐   │
│  │ Doc Parser │  │ RAG Service│  │ LLM Service (Ollama)   │   │
│  │ PDF/DOCX/  │  │ Qdrant     │  │ llama3.2 extract JSON  │   │
│  │ TXT        │  │ embeddings │  └────────────────────────┘   │
│  └────────────┘  └─────┬──────┘                                │
└────────────────────────┼────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
┌────────┐         ┌──────────┐         ┌──────────┐
│Postgres│         │  Qdrant  │         │  Ollama  │
│  :5432 │         │  :6333   │         │  :11434  │
└────────┘         └──────────┘         └──────────┘
```

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)
- 8 GB RAM recommended (for running the local LLM)

### Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd <repo-directory>

# 2. Start all services (builds images, starts containers)
./scripts/start.sh

# 3. Pull the Ollama model (first run only — ~2 GB download)
docker compose exec ollama ollama pull llama3.2

# 4. (Optional) Seed sample master data
python3 scripts/seed_master_data.py
```

The startup script copies `.env.example` → `.env` automatically on first run. Edit `.env` to change passwords before running in production.

---

## Service URLs

| Service      | URL                              | Description                  |
|--------------|----------------------------------|------------------------------|
| Frontend     | http://localhost:3000            | React web UI                 |
| Backend API  | http://localhost:8000            | FastAPI REST API              |
| API Docs     | http://localhost:8000/docs       | Swagger / OpenAPI            |
| Qdrant UI    | http://localhost:6333/dashboard  | Vector store dashboard       |
| Ollama API   | http://localhost:11434           | Local LLM inference          |

---

## Usage

### Uploading Purchase Orders

1. Open http://localhost:3000
2. On the **Orders** page, drag-and-drop or click to upload a PDF, DOCX, or TXT purchase order.
3. The pipeline automatically:
   - Extracts text from the document
   - Uses the local LLM to identify vendor, PO number, date, and line items
   - Matches each line item against the master catalogue via vector search
   - Calculates a confidence score for each line and for the whole PO
4. The PO appears in the queue with status **Under Review**.

### Reviewing Orders

1. Click **Review →** on any order.
2. The detail page shows extracted header info and an editable line-items table.
3. Click any cell to edit matched item codes, quantities, UOMs, or prices.
4. Click **Approve** or **Reject**.
5. Approved orders have a **Download XML** button.

### Managing Master Data

1. Go to **Master Data** in the navigation.
2. Use the **Items** tab to upload your product catalogue CSV and view/delete items.
3. Use the **Units of Measure** tab to upload your UOM CSV.
4. Download template CSVs using the link on each tab.

---

## API Overview

| Method | Endpoint                              | Description                   |
|--------|---------------------------------------|-------------------------------|
| POST   | `/api/orders/upload`                  | Upload & process PO document  |
| GET    | `/api/orders`                         | List all POs (paginated)      |
| GET    | `/api/orders/{id}`                    | Get full PO with lines        |
| PATCH  | `/api/orders/{id}`                    | Update PO status/data         |
| PATCH  | `/api/orders/{id}/lines/{line_id}`    | Update a PO line              |
| POST   | `/api/orders/{id}/approve`            | Approve PO                    |
| POST   | `/api/orders/{id}/reject`             | Reject PO                     |
| GET    | `/api/export/orders/{id}/xml`         | Download ERP XML              |
| POST   | `/api/master-data/items/upload`       | Bulk upload items CSV         |
| GET    | `/api/master-data/items`              | List items                    |
| POST   | `/api/master-data/items`              | Create single item            |
| DELETE | `/api/master-data/items/{id}`         | Delete item                   |
| POST   | `/api/master-data/uoms/upload`        | Bulk upload UOMs CSV          |
| GET    | `/api/master-data/uoms`               | List UOMs                     |
| POST   | `/api/master-data/uoms`               | Create single UOM             |
| DELETE | `/api/master-data/uoms/{id}`          | Delete UOM                    |

---

## Master Data

### Items CSV format (`templates/items_template.csv`)

```
code,description,unit_of_measure,unit_price,category
BOLT-M6,M6 Hex Bolt 50mm,EA,0.25,Fasteners
```

| Column           | Required | Description                        |
|------------------|----------|------------------------------------|
| code             | ✅       | Unique item code                   |
| description      | ✅       | Item description (used for search) |
| unit_of_measure  | ✅       | Default UOM code                   |
| unit_price       |          | Numeric unit price                 |
| category         |          | Item category                      |

### UOMs CSV format (`templates/uom_template.csv`)

```
code,description,aliases
EA,Each,each;piece;unit;no;nos
```

| Column      | Required | Description                               |
|-------------|----------|-------------------------------------------|
| code        | ✅       | Unique UOM code                           |
| description | ✅       | Full name                                 |
| aliases     |          | Semicolon-separated alternate spellings   |

---

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` and edit:

| Variable            | Default                                              | Description                   |
|---------------------|------------------------------------------------------|-------------------------------|
| `POSTGRES_PASSWORD` | `changeme`                                           | Database password             |
| `POSTGRES_DB`       | `po_pipeline`                                        | Database name                 |
| `POSTGRES_USER`     | `po_user`                                            | Database user                 |
| `DATABASE_URL`      | `postgresql://po_user:changeme@postgres:5432/...`    | Full SQLAlchemy URL           |
| `QDRANT_URL`        | `http://qdrant:6333`                                 | Qdrant vector store URL       |
| `OLLAMA_URL`        | `http://ollama:11434`                                | Ollama LLM server URL         |
| `OLLAMA_MODEL`      | `llama3.2`                                           | Ollama model name             |
| `SECRET_KEY`        | `change-me-in-production`                            | App secret (JWT future use)   |

---

## Azure Deployment

To deploy on Azure:

1. **Azure Container Apps** — push images to Azure Container Registry, deploy each service as a Container App within the same environment (shared VNet for service discovery).
2. **Azure Database for PostgreSQL** — replace the `postgres` service with a managed instance; update `DATABASE_URL`.
3. **Persistent storage** — map `qdrant_data` and `ollama_data` volumes to Azure Files shares.
4. **Secrets** — store `.env` values in Azure Key Vault and reference them as Container App secrets.
5. **GPU SKU** — for faster LLM inference, deploy the `ollama` service on a GPU-enabled Container App environment.

---

## Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start dependencies (Postgres, Qdrant, Ollama) separately, then:
export DATABASE_URL="postgresql://po_user:changeme@localhost:5432/po_pipeline"
export QDRANT_URL="http://localhost:6333"
export OLLAMA_URL="http://localhost:11434"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173 with proxy to backend at :8000
```
