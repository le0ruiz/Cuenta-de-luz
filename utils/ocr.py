import streamlit as st
import numpy as np
from PIL import Image
import re
import easyocr

# Inicializar el lector OCR (solo una vez, se cachea)
@st.cache_resource
def get_ocr_reader():
    """Inicializa y cachea el lector EasyOCR"""
    # 'es' para español, 'en' para inglés (necesario para números)
    return easyocr.Reader(['es', 'en'], gpu=False)

def process_meter_image(image_file):
    """
    Extrae números de un medidor usando EasyOCR.
    Retorna la lectura como entero o None si no encuentra números válidos.
    """
    try:
        # Cargar la imagen
        image = Image.open(image_file)
        # Convertir a array numpy (EasyOCR lo necesita)
        image_np = np.array(image)
        
        # Obtener el lector cacheado
        reader = get_ocr_reader()
        
        # Realizar OCR
        result = reader.readtext(image_np)
        
        # Extraer todos los números detectados
        numbers = []
        for detection in result:
            text = detection[1]  # El texto reconocido
            # Buscar números enteros en el texto
            nums = re.findall(r'\b\d+\b', text)
            numbers.extend([int(n) for n in nums])
        
        if not numbers:
            return None
        
        # Filtrar números que parecen lecturas de medidor (100-99999)
        # Los medidores suelen tener 3-5 dígitos
        valid = [n for n in numbers if 100 <= n <= 99999]
        if valid:
            # Si hay múltiples, tomar el más grande (suele ser la lectura actual)
            return max(valid)
        
        # Si no hay válidos, devolver el número más grande encontrado
        return max(numbers)
    
    except Exception as e:
        st.error(f"Error al procesar la imagen del medidor: {e}")
        return None

def extract_total_amount_from_bill(image_file):
    """
    Extrae el monto total de una boleta usando EasyOCR.
    Retorna el monto como float o None si no lo encuentra.
    """
    try:
        # Cargar la imagen
        image = Image.open(image_file)
        image_np = np.array(image)
        
        # Obtener el lector cacheado
        reader = get_ocr_reader()
        
        # Realizar OCR
        result = reader.readtext(image_np)
        
        # Unir todo el texto reconocido
        full_text = " ".join([detection[1] for detection in result])
        
        # Patrones para buscar el monto total
        patterns = [
            r'\$\s*([\d,]+\.?\d*)',           # $123,456.78
            r'total\s*[:]?\s*\$\s*([\d,]+\.?\d*)',  # Total: $123,456.78
            r'monto\s*[:]?\s*\$\s*([\d,]+\.?\d*)',  # Monto: $123,456.78
            r'importe\s*[:]?\s*\$\s*([\d,]+\.?\d*)', # Importe: $123,456.78
            r'valor\s*[:]?\s*\$\s*([\d,]+\.?\d*)',   # Valor: $123,456.78
            r'pag[oó]\s*[:]?\s*\$\s*([\d,]+\.?\d*)', # Pagó: $123,456.78
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        # Si no se encontró con patrones, buscar el número más grande (suele ser el total)
        numbers = re.findall(r'[\d,]+\.?\d*', full_text)
        floats = []
        for n in numbers:
            try:
                floats.append(float(n.replace(',', '')))
            except ValueError:
                continue
        
        if floats:
            # El número más grande suele ser el total
            return max(floats)
        
        return None
    
    except Exception as e:
        st.error(f"Error al procesar la boleta: {e}")
        return None
