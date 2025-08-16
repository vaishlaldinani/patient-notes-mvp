import os, io, hashlib, tempfile, shutil
from typing import Tuple, Optional
from PIL import Image
import pytesseract

# pdf2image requires poppler installed on system
from pdf2image import convert_from_path

ALLOWED_MIME = {
    'application/pdf',
    'image/png',
    'image/jpeg',
    'image/jpg',
}

def sha256_file(path:str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def ocr_file_to_text(file_path:str, mime:str) -> Tuple[str, Optional[float]]:
    """Return (text, avg_confidence) using Tesseract. Supports PDF and images.
    For PDFs, renders pages to images via poppler and concatenates results.
    """
    if mime not in ALLOWED_MIME:
        raise ValueError(f"Unsupported mime type: {mime}")

    if mime == 'application/pdf':
        pages = convert_from_path(file_path, dpi=300)
        texts, confs = [], []
        for page in pages:
            txt = pytesseract.image_to_string(page)
            data = pytesseract.image_to_data(page, output_type=pytesseract.Output.DICT)
            # Compute average confidence excluding -1
            vals = [c for c in data.get('conf', []) if isinstance(c, (int,float)) and c >= 0]
            conf = sum(vals)/len(vals) if vals else None
            texts.append(txt)
            if conf is not None:
                confs.append(conf)
        all_text = "\n\n".join(texts).strip()
        avg_conf = sum(confs)/len(confs) if confs else None
        return all_text, avg_conf
    else:
        image = Image.open(file_path)
        txt = pytesseract.image_to_string(image)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        vals = [c for c in data.get('conf', []) if isinstance(c, (int,float)) and c >= 0]
        conf = sum(vals)/len(vals) if vals else None
        return txt.strip(), conf
