import io
import os
import math
import uuid
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps, ExifTags

from app.core.config import settings
from app.core.constants import MAX_IMAGE_DIMENSION
from app.core.logger import logger

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None


def _auto_rotate_exif(image: Image.Image) -> Image.Image:
    """Koreksi orientasi berdasarkan metadata EXIF (foto dari HP)."""
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass
    return image


def _deskew(cv_image: np.ndarray) -> np.ndarray:
    """
    Mendeteksi kemiringan teks pada gambar dan mengkoreksinya.
    Menggunakan Hough Line Transform untuk estimasi sudut.
    """
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)

    if lines is None:
        return cv_image

    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 != x1:
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            if -45 < angle < 45:
                angles.append(angle)

    if not angles:
        return cv_image

    median_angle = float(np.median(angles))
    if abs(median_angle) < 0.5:
        return cv_image

    logger.info(f"[ImageService] Mendeteksi kemiringan {median_angle:.2f}° - melakukan koreksi deskew")
    h, w = cv_image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    corrected = cv2.warpAffine(cv_image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return corrected


def _resize_if_needed(image: Image.Image) -> Image.Image:
    """Resize gambar jika dimensi melebihi MAX_IMAGE_DIMENSION agar OCR tidak OOM."""
    w, h = image.size
    if max(w, h) > MAX_IMAGE_DIMENSION:
        ratio = MAX_IMAGE_DIMENSION / max(w, h)
        new_size = (int(w * ratio), int(h * ratio))
        logger.info(f"[ImageService] Resize gambar dari {w}x{h} → {new_size[0]}x{new_size[1]}")
        image = image.resize(new_size, Image.LANCZOS)
    return image


def preprocess_image(file_bytes: bytes) -> tuple[Image.Image, str]:
    """
    Pipeline preprocessing lengkap:
    1. Buka gambar dari bytes
    2. Koreksi EXIF
    3. Konversi ke RGB
    4. Resize jika perlu
    5. Deskew via OpenCV
    6. Simpan ke temp file, return (PIL Image, temp_path)
    """
    # 1. Buka & koreksi EXIF
    pil_image = Image.open(io.BytesIO(file_bytes))
    pil_image = _auto_rotate_exif(pil_image)
    pil_image = pil_image.convert("RGB")

    # 2. Resize
    pil_image = _resize_if_needed(pil_image)

    # 3. Deskew via OpenCV
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    cv_image = _deskew(cv_image)
    pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

    # 4. Simpan ke temp
    temp_dir = Path(settings.temp_folder)
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = str(temp_dir / f"{uuid.uuid4().hex}.jpg")
    pil_image.save(temp_path, "JPEG", quality=95)

    logger.info(f"[ImageService] Gambar disimpan sementara ke: {temp_path}")
    return pil_image, temp_path


def convert_pdf_to_images(file_bytes: bytes) -> list[tuple[Image.Image, str]]:
    """
    Ekstrak halaman PDF menjadi list of (PIL Image, temp_path).
    Setiap halaman diperlakukan sebagai satu gambar terpisah.
    """
    if pdfium is None:
        raise RuntimeError("pypdfium2 tidak terinstall. Jalankan pip install pypdfium2")
        
    pdf = pdfium.PdfDocument(file_bytes)
    results = []
    
    logger.info(f"[ImageService] Mengekstrak {len(pdf)} halaman dari dokumen PDF.")
    
    for i in range(len(pdf)):
        page = pdf.get_page(i)
        # Render at 300 DPI
        pil_image = page.render(scale=300/72).to_pil()
        
        # 1. Koreksi EXIF / Convert
        pil_image = pil_image.convert("RGB")
        
        # 2. Resize
        pil_image = _resize_if_needed(pil_image)
        
        # 3. Deskew
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        cv_image = _deskew(cv_image)
        pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        
        # 4. Simpan ke temp
        temp_dir = Path(settings.temp_folder)
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = str(temp_dir / f"{uuid.uuid4().hex}_page_{i+1}.jpg")
        pil_image.save(temp_path, "JPEG", quality=95)
        
        results.append((pil_image, temp_path))
        
    return results


def cleanup_temp(temp_path: str) -> None:
    """Hapus file temporer setelah selesai diproses."""
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.debug(f"[ImageService] Temp file dihapus: {temp_path}")
    except Exception as e:
        logger.warning(f"[ImageService] Gagal hapus temp file: {e}")
