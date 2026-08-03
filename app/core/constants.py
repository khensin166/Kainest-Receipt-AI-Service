# Tipe file gambar yang didukung
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif", "application/pdf"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".pdf"}

# Bahasa OCR yang disupport (Surya: kode ISO 639-1)
OCR_LANGUAGES = ["id", "en"]

# Batas ukuran gambar untuk OCR (piksel) - resize jika lebih besar
MAX_IMAGE_DIMENSION = 1280

# Batch size untuk akselerasi eksekusi Surya OCR pada CPU
OCR_RECOGNITION_BATCH_SIZE = 32
OCR_DETECTION_BATCH_SIZE = 16

# Threshold score konfiden minimum dari OCR
MIN_OCR_CONFIDENCE = 0.5

# Tolerance aritmatika validasi (dalam Rupiah)
VALIDATION_TOLERANCE_IDR = 100

