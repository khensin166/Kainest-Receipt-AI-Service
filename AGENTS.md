# Kainest Receipt AI Service & Split Bill Engine
## Agent Handoff Notes

### Tanggal Dibuat: 03 Agustus 2026

---

## Deskripsi Proyek

**Kainest Receipt AI Service** adalah microservice independen berbasis **Python FastAPI** yang berfungsi sebagai _engine_ untuk:

1. **Scan & Ekstraksi Struk** — Mengubah foto struk belanja (JPG/PNG/WEBP/HEIC) menjadi data JSON terstruktur menggunakan **Surya OCR** dan **Groq LLM**.
2. **Split Bill Engine** — Menghitung pembagian tagihan antar anggota (mode _Itemized_ dan _Bagi Rata_) dengan alokasi pajak proporsional.

Proyek ini **stateless** (tanpa database) dan berdiri sendiri dari repositori Kainest BE/FE.

---

## Arsitektur & Alur Sistem

![Diagram Alur Service](docs/flow_diagram.png)

### Alur 2 Tahap (Integrasi dengan Kainest Frontend)

```
TAHAP 1: SCAN & EXTRACT
=====================================================
User → Upload Foto Struk (JPG/PNG)
    → FastAPI POST /receipt/scan
    → [Image Service] EXIF auto-rotate, deskew, resize
    → [OCR Service] Surya DetectionPredictor + RecognitionPredictor
    → Raw OCR Text (baris teks + bounding box + confidence)
    → [Parser Service] Groq LLM (llama-3.3-70b) + Prompt Markdown
    → JSON Terstruktur (merchant, items, subtotal, tax, total)
    → [Validation Service] Cek aritmatika, auto-koreksi jika perlu
    → Response: { code, status, confidence, data: { items: [...] } }

TAHAP 2: ASSIGN & SPLIT BILL
=====================================================
Frontend → Tampilkan daftar item hasil scan ke user
User     → Tambahkan nama anggota (misal: Budi, Ani, Caca)
User     → Pilih MODE:
           ├─ "itemized": Drag/assign item ke orang tertentu
           └─ "equal": Klik "Bagi Rata"
    → FastAPI POST /receipt/split
    → [Split Service] Hitung proporsional tax/service/discount per anggota
    → Response: breakdown per anggota + summary_text siap salin ke WA
```

### Formula Alokasi Pajak (Itemized Mode)
```
Pajak_Anggota_A = (Subtotal_Anggota_A / Subtotal_Total) × Total_Pajak
```
Selisih pembulatan (Rp 1-2) dialokasikan ke anggota pertama.

---

## Struktur Proyek

```
Receipt_Ai_Service/
├── app/
│   ├── api/
│   │   ├── health.py         # GET /health
│   │   ├── receipt.py        # POST /receipt/scan
│   │   └── split.py          # POST /receipt/split
│   ├── core/
│   │   ├── config.py         # Pydantic-settings env management
│   │   ├── logger.py         # Loguru dengan rotasi harian
│   │   └── constants.py      # Konstanta global
│   ├── models/
│   │   ├── request.py        # SplitBillRequest, ItemAssignment
│   │   └── response.py       # ReceiptScanResponse, SplitBillResponse, dll.
│   ├── services/
│   │   ├── image_service.py      # Preprocessing (EXIF, deskew, resize)
│   │   ├── ocr_service.py        # Surya OCR runner (Singleton predictor)
│   │   ├── parser_service.py     # Groq API client + prompt runner
│   │   ├── validation_service.py # Aritmatika checker + auto-koreksi
│   │   ├── split_service.py      # Engine split bill (itemized & equal)
│   │   └── receipt_service.py    # Orchestrator pipeline utama
│   ├── prompts/
│   │   └── receipt_parser.md     # Prompt Markdown untuk Groq (edit bebas tanpa ubah kode)
│   └── main.py                   # FastAPI entry point, CORS, lifespan pre-load
├── docs/
│   └── flow_diagram.png          # Diagram alur service
├── uploads/                      # Temp folder (auto-cleanup setelah setiap request)
├── logs/                         # Log Loguru (rotasi harian, retain 7 hari)
├── tests/
│   ├── test_health.py
│   ├── test_validation.py
│   └── test_split.py
├── .env.example
├── Dockerfile
└── requirements.txt
```

---

## Cara Menjalankan Lokal

```bash
# 1. Clone / masuk ke folder
cd "Receipt_Ai_Service"

# 2. Buat virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# atau: source venv/bin/activate  (Linux/Mac)

# 3. Install PyTorch CPU-only DAHULU (agar tidak download versi CUDA 3GB+)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 4. Install dependencies lainnya
pip install -r requirements.txt

# 5. Salin dan isi .env
cp .env.example .env
# Edit .env: isi GROQ_API_KEY

# 6. Jalankan service
uvicorn app.main:app --reload --port 8000

# 7. Buka Swagger UI
# http://localhost:8000/docs
```

---

## Environment Variables

| Variable | Wajib | Default | Keterangan |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ | — | API Key dari console.groq.com |
| `GROQ_MODEL` | — | `llama-3.3-70b-versatile` | Model Groq yang digunakan |
| `TORCH_DEVICE` | — | `cpu` | `cpu` atau `cuda` |
| `TEMP_FOLDER` | — | `uploads` | Folder penyimpanan file sementara |
| `MAX_IMAGE_SIZE_MB` | — | `10` | Maksimum ukuran file gambar |
| `LOG_LEVEL` | — | `INFO` | Level logging: DEBUG/INFO/WARNING |

---

## API Endpoints

### `GET /health`
Cek status service.

### `POST /receipt/scan`
- **Form-Data**: `image` (File JPG/PNG/WEBP/HEIC, maks 10MB)
- **Response**: JSON dengan field `code`, `status`, `confidence` (0.0–1.0), dan `data` berisi detail struk.

### `POST /receipt/split`
- **Body JSON**: `mode`, `members`, `subtotal`, `tax`, `service`, `discount`, `total`, `assignments` (jika mode=itemized)
- **Response**: JSON dengan breakdown bayar per anggota dan `summary_text` siap salin ke WhatsApp.

---

## Tech Stack

| Komponen | Teknologi |
|---|---|
| API Framework | FastAPI + Uvicorn |
| OCR Engine | Surya OCR (datalab-to/surya) |
| LLM Parser | Groq API (llama-3.3-70b-versatile) |
| Image Processing | Pillow + OpenCV (headless) |
| Config Management | Pydantic-Settings |
| Logging | Loguru |
| Testing | pytest |
| Container | Docker (CPU-only PyTorch) |

---

## Catatan untuk Agent Selanjutnya

1. **Surya OCR Predictors** diinisialisasi sebagai _Singleton_ (dimuat sekali saat startup) untuk efisiensi memory. Jangan re-inisialisasi di setiap request.
2. **Prompt Markdown** di `app/prompts/receipt_parser.md` dapat diedit bebas tanpa menyentuh kode Python — ini adalah desain yang disengaja untuk kemudahan tuning.
3. **Deskewing** di `image_service.py` menggunakan Hough Line Transform. Jika struk sangat kusut (miring > 45°), perlu ditambahkan logika rotasi 90°/180° berdasarkan deteksi orientasi teks.
4. **Selisih pembulatan** pada Split Bill dialokasikan ke anggota pertama dalam list — ini sudah by design dan jumlahnya maksimal Rp (jumlah_anggota - 1).
5. **CORS** saat ini di-set `allow_origins=["*"]`. Di production, ganti dengan domain spesifik Kainest Frontend.
6. **Roadmap Selanjutnya**:
   - Phase 3: Docker Compose multi-service (dengan Redis Queue jika traffic tinggi)
   - Integrasi ke Kainest BE sebagai proxy endpoint (`POST /budget/receipt/scan`)
   - Fitur simpan hasil scan ke database transaksi Kainest secara langsung
