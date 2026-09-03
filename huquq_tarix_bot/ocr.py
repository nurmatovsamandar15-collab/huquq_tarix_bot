import re
import io
from dataclasses import dataclass
from typing import Optional
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import easyocr
    reader = easyocr.Reader(['en', 'uz'], gpu=False)
except Exception:
    reader = None

@dataclass
class OCRResult:
    amount: Optional[int]
    transaction_id: Optional[str]
    is_valid_amount: bool
    raw_text: str

async def parse_receipt(image_bytes: bytes, min_amount: int = 18000, max_amount: int = 25000) -> OCRResult:
    text = ""
    
    # 1. EasyOCR orqali o'qish
    if reader is not None:
        try:
            results = reader.readtext(image_bytes, detail=0)
            text = " ".join(results)
        except Exception:
            text = ""

    # 2. Agar EasyOCR o'qiy olmasa, PyTesseract (Fallback)
    if not text.strip() and pytesseract is not None:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(img)
        except Exception:
            text = ""

    # Summa regex namunalari (UzSUM, so'm, va h.k.)
    amount = None
    amounts = re.findall(r'(\d[\d\s\.,]{2,10})\s*(?:сум|so\'m|som|uzs)', text, re.IGNORECASE)
    for amt_str in amounts:
        clean_amt = re.sub(r'[^\d]', '', amt_str)
        if clean_amt:
            val = int(clean_amt)
            if 1000 <= val <= 10000000:
                amount = val
                break

    # Tranzaksiya ID (Order ID, Ref, Tranzaksiya ID)
    tx_id = None
    tx_patterns = [
        r'(?:Order ID|ID|Ref|Tranzaksiya|Check|Chek)\s*[:#-]?\s*([A-Za-z0-9_-]{6,25})',
        r'\b(\d{8,20})\b'
    ]
    for pattern in tx_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            tx_id = match.group(1)
            break

    is_valid = False
    if amount and (min_amount <= amount <= max_amount):
        is_valid = True

    return OCRResult(
        amount=amount,
        transaction_id=tx_id,
        is_valid_amount=is_valid,
        raw_text=text
    )