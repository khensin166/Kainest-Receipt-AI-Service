# Kainest Receipt AI Service & Split Bill Engine

> Microservice independen untuk ekstraksi struk belanja via OCR + LLM dan kalkulasi Split Bill.

![Architecture Flow](docs/flow_diagram.png)

## Features
- 📷 **Scan Struk** — Upload foto struk → JSON terstruktur (OCR Surya + Groq LLM)
- ✂️ **Split Bill Itemized** — Assign item tertentu ke orang tertentu, pajak proporsional
- ➗ **Split Bill Bagi Rata** — Bagi total merata ke semua anggota
- 📊 **Confidence Score** — Skor akurasi gabungan OCR + LLM parsing (0.0–1.0)
- 📋 **WA Shareable Text** — Response siap salin ke grup WhatsApp

## Quick Start

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cp .env.example .env  # isi GROQ_API_KEY
uvicorn app.main:app --reload
# Buka: http://localhost:8000/docs
```

## Documentation
Lihat [AGENTS.md](AGENTS.md) untuk dokumentasi teknis lengkap dan catatan handoff agent.

## Tech Stack
FastAPI · Surya OCR · Groq LLM · OpenCV · Pydantic v2 · Loguru · pytest
