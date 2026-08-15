import easyocr
import streamlit as st

# Inicializar lector OCR (solo una vez, para optimizar)
@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(['es', 'en'])  # Soporta español e inglés

def process_meter_image(image_file):
    """Extrae números de un medidor usando EasyOCR (gratuito)"""
    try:
        reader = get_ocr_reader()
        # Guardar la imagen temporalmente
        import tempfile
        import os
        from PIL import Image
        
        # EasyOCR necesita la ruta del archivo o un array numpy
        image = Image.open(image_file)
        import numpy as np
        image_np = np.array(image)
        
        # Realizar OCR
        result = reader.readtext(image_np)
        
        # Extraer solo números
        import re
        numbers = []
        for detection in result:
            text = detection[1]  # El texto detectado
            # Buscar números en el texto
            nums = re.findall(r'\b\d+\b', text)
            numbers.extend([int(n) for n in nums])
        
        if not numbers:
            return None
        
        # Filtrar números que parecen lecturas de medidor (100-99999)
        valid = [n for n in numbers if 100 <= n <= 99999]
        if valid:
            return max(valid)
        return max(numbers)
    except Exception as e:
        st.error(f"Error en OCR: {e}")
        return None

def extract_total_amount_from_bill(image_file):
    """Extrae el monto total de una boleta usando EasyOCR"""
    try:
        reader = get_ocr_reader()
        from PIL import Image
        import numpy as np
        import re
        
        image = Image.open(image_file)
        image_np = np.array(image)
        result = reader.readtext(image_np)
        
        # Unir todo el texto
        full_text = " ".join([detection[1] for detection in result])
        
        # Buscar patrones de dinero
        patterns = [
            r'\$\s*([\d,]+\.?\d*)',
            r'total\s*[:]?\s*\$\s*([\d,]+\.?\d*)',
            r'monto\s*[:]?\s*\$\s*([\d,]+\.?\d*)',
            r'importe\s*[:]?\s*\$\s*([\d,]+\.?\d*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        # Si no, buscar el número más grande
        numbers = re.findall(r'[\d,]+\.?\d*', full_text)
        floats = []
        for n in numbers:
            try:
                floats.append(float(n.replace(',', '')))
            except ValueError:
                continue
        if floats:
            return max(floats)
        return None
    except Exception as e:
        st.error(f"Error procesando boleta: {e}")
        return None
