import pandas as pd
from datetime import datetime

def calculate_bill(
    previous_reading_f, current_reading_f,
    previous_reading_g, current_reading_g,
    previous_general, current_general,
    total_bill_amount
):
    consumption_f = current_reading_f - previous_reading_f if current_reading_f and previous_reading_f else 0
    consumption_g = current_reading_g - previous_reading_g if current_reading_g and previous_reading_g else 0
    total_consumption = consumption_f + consumption_g
    general_diff = current_general - previous_general if current_general and previous_general else 0
    if total_consumption > 0 and abs(total_consumption - general_diff) > 10:
        effective_total = total_consumption
        warning = "⚠️ La suma de consumos de departamentos no coincide con el medidor general. Se usará la suma de departamentos."
    else:
        effective_total = max(total_consumption, general_diff)
        warning = None
    if effective_total == 0 or total_bill_amount == 0:
        return {
            "consumption_f": consumption_f,
            "consumption_g": consumption_g,
            "total_consumption": effective_total,
            "cost_f": 0,
            "cost_g": 0,
            "total_bill": total_bill_amount,
            "warning": "No hay consumo o monto de boleta = 0."
        }
    cost_f = (consumption_f / effective_total) * total_bill_amount if effective_total > 0 else 0
    cost_g = (consumption_g / effective_total) * total_bill_amount if effective_total > 0 else 0
    cost_f = round(cost_f, 2)
    cost_g = round(cost_g, 2)
    diff = total_bill_amount - (cost_f + cost_g)
    if abs(diff) > 0.01:
        if cost_f >= cost_g:
            cost_f = round(cost_f + diff, 2)
        else:
            cost_g = round(cost_g + diff, 2)
    return {
        "consumption_f": consumption_f,
        "consumption_g": consumption_g,
        "total_consumption": effective_total,
        "general_diff": general_diff,
        "cost_f": cost_f,
        "cost_g": cost_g,
        "total_bill": total_bill_amount,
        "warning": warning,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

def generate_report(result, readings):
    report = f"""
    📊 INFORME DE ELECTRICIDAD
    {'='*40}
    
    📅 Fecha: {result['date']}
    
    📈 CONSUMO:
    • Depto F: {result['consumption_f']} kWh
    • Depto G: {result['consumption_g']} kWh
    • Total: {result['total_consumption']} kWh
    
    💰 COSTOS:
    • Depto F: ${result['cost_f']:,.2f}
    • Depto G: ${result['cost_g']:,.2f}
    • Total boleta: ${result['total_bill']:,.2f}
    
    📋 LECTURAS:
    • Medidor F: {readings.get('f_current', 'N/A')} (prev: {readings.get('f_previous', 'N/A')})
    • Medidor G: {readings.get('g_current', 'N/A')} (prev: {readings.get('g_previous', 'N/A')})
    • Medidor general: {readings.get('general_current', 'N/A')} (prev: {readings.get('general_previous', 'N/A')})
    """
    if result.get('warning'):
        report += f"\n⚠️ {result['warning']}"
    return report
