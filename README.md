# 📄 Layout-Aware OCR for Contract Data Extraction

A FastAPI-powered pipeline that extracts structured data from contract PDFs using layout analysis, OCR, and LLM-based field extraction.

## ⚙️ How It Works

```
PDF Upload → Layout Detection (Docling) → Region Cropping → OCR (PaddleOCR) → LLM Extraction (Groq) → Structured JSON
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **API Framework** | FastAPI + Uvicorn |
| **Layout Analysis** | Docling (reading order, tables, annotations) |
| **PDF Rendering** | pypdfium2 + Pillow |
| **OCR Engine** | PaddleOCR / PaddlePaddle |
| **LLM Extraction** | Groq API (via OpenAI SDK) |
| **Validation** | Pydantic v2 |

## 🚀 Setup

### 1. Clone & Create Virtual Environment

```bash
git clone <repo-url>
cd Layout-Aware-OCR-for-Document-Intelligence

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```
GROQ_API_KEY=your-groq-api-key-here
```

## ▶️ Usage

### API Server

```bash
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

### CLI (Batch Processing)

Drop PDF files into the `raw_pdfs/` folder, then run:

```bash
python -m app.cli
```

All PDFs in the folder will be processed automatically.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/process-pdf` | Upload & process a contract PDF |
| `GET` | `/stems` | List all processed document stems |
| `GET` | `/annotated-pdf/{stem}` | Download PDF with layout annotations |
| `GET` | `/raw-extracted-text/{stem}` | Get raw OCR text as JSON |
| `GET` | `/llm-structured-json/{stem}` | Get LLM-extracted structured fields |
| `GET` | `/health` | Health check |

### Extracted Fields

```json
{
  "contractor_name": "...",
  "contractor_no": "...",
  "vat_number": "...",
  "process_date": "...",
  "gross_pay": 0.0,
  "net_pay": 0.0
}
```

## 📁 Project Structure

```
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py             # Settings & env loading
│   ├── schemas.py            # Pydantic models
│   ├── cli.py                # CLI batch processor
│   ├── api/
│   │   └── documents.py      # API route handlers
│   └── services/
│       ├── pipeline.py       # Main processing pipeline
│       ├── layout.py         # Docling layout extraction
│       ├── ocr.py            # PaddleOCR wrapper
│       ├── cropper.py        # PDF region cropping
│       ├── extraction.py     # LLM field extraction
│       └── store.py          # File storage manager
├── raw_pdfs/                 # Input PDFs (CLI mode)
├── processed_pdf/            # Annotated output PDFs
├── json/                     # Layout JSON outputs
├── markdown/                 # Markdown exports
├── storage/                  # Cropped region images
├── requirements.txt
└── .env
```

## 👤 Author

**Ali Zain** — [LinkedIn](https://www.linkedin.com/in/alizain-technologist)
