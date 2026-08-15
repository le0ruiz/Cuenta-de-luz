import io
import os
import re
from PIL import Image
from google.cloud import vision
from google.oauth2 import service_account
import streamlit as st

def get_vision_client():
    if "GCP_CREDENTIALS" in st.secrets:
        creds_dict = st.secrets["GCP_CREDENTIALS"]
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        return vision.ImageAnnotatorClient(credentials=credentials)
    elif os.path.exists("credentials.json"):
        credentials = service_account.Credentials.from_service_account_file("credentials.json")
        return vision.ImageAnnotatorClient(credentials=credentials)
    else:
        st.warning("⚠️ Credenciales de Google Cloud Vision no encontradas. OCR desactivado.")
        return None

def extract_numbers_from_image(image_file):
    client = get_vision_client()
    if client is None:
        return []
    content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if not texts:
        return []
    full_text = texts[0].description
    numbers = re.findall(r'\b\d+\b', full_text)
    numbers = [int(n) for n in numbers]
    return numbers

def extract_total_amount_from_bill(image_file):
    client = get_vision_client()
    if client is None:
        return None
    content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if not texts:
        return None
    full_text = texts[0].description
    patterns = [
        r'\$\s*([\d,]+\.?\d*)',
        r'total\s*[:]?\s*\$\s*([\d,]+\.?\d*)',
        r'monto\s*[:]?\s*\$\s*([\d,]+\.?\d*)',
        r'importe\s*[:]?\s*\$\s*([\d,]+\.?\d*)',
        r'valor\s*[:]?\s*\$\s*([\d,]+\.?\d*)',
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                continue
    numbers = re.findall(r'\$?\s*([\d,]+\.?\d*)', full_text)
    if numbers:
        floats = []
        for n in numbers:
            try:
                floats.append(float(n.replace(',', '')))
            except ValueError:
                continue
        if floats:
            return max(floats)
    return None

def process_meter_image(image_file):
    numbers = extract_numbers_from_image(image_file)
    if not numbers:
        return None
    valid = [n for n in numbers if 100 <= n <= 99999]
    if valid:
        return max(valid)
    return max(numbers) if numbers else None
