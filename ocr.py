import io
import os
from PIL import Image
from google.cloud import vision
from google.oauth2 import service_account
import streamlit as st

# Google Cloud Vision client (uses credentials from environment or secrets)
def get_vision_client():
    credentials = None
    if "GCP_CREDENTIALS" in st.secrets:
        creds_dict = st.secrets["GCP_CREDENTIALS"]
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
    elif os.path.exists("credentials.json"):
        credentials = service_account.Credentials.from_service_account_file("credentials.json")
    else:
        st.warning("⚠️ Google Cloud Vision credentials not found. OCR will be disabled.")
        return None
    return vision.ImageAnnotatorClient(credentials=credentials)

def extract_numbers_from_image(image_file):
    """
    Extracts numbers from an image using Google Cloud Vision.
    Returns a list of integers found in the image.
    """
    client = get_vision_client()
    if client is None:
        return []
    
    content = image_file.read()
    image = vision.Image(content=content)
    
    # Text detection
    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    if not texts:
        return []
    
    # The first annotation is the full text, others are individual words
    full_text = texts[0].description
    # Extract all numbers (integers)
    import re
    numbers = re.findall(r'\b\d+\b', full_text)
    # Convert to integers
    numbers = [int(n) for n in numbers]
    return numbers

def extract_total_amount_from_bill(image_file):
    """
    Extracts the total amount (with $ sign) from a bill image.
    Returns the total amount as a float, or None if not found.
    """
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
    # Look for patterns like "$123,456" or "$123.456" or "Total: $123"
    import re
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
    # If no pattern matches, try to find the largest number (often the total)
    numbers = re.findall(r'\$?\s*([\d,]+\.?\d*)', full_text)
    if numbers:
        # Filter out small numbers, take the largest as total
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
    """
    Process meter image: try to find the most likely reading.
    Returns the reading as an integer, or None.
    """
    numbers = extract_numbers_from_image(image_file)
    if not numbers:
        return None
    # For a meter, the reading is usually the largest number or the one with 4-5 digits
    # Filter numbers that are reasonable for a meter reading (e.g., 100-99999)
    valid = [n for n in numbers if 100 <= n <= 99999]
    if valid:
        # If multiple, take the largest (most likely the current reading)
        return max(valid)
    # If no valid numbers, return the largest number found
    return max(numbers) if numbers else None
