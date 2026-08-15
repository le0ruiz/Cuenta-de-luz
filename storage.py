import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import pandas as pd
from datetime import datetime

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def get_gsheet_client():
    try:
        if "GSHEET_CREDENTIALS" in st.secrets:
            creds_dict = st.secrets["GSHEET_CREDENTIALS"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        elif "GSHEET_CREDENTIALS_FILE" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                st.secrets["GSHEET_CREDENTIALS_FILE"], SCOPE
            )
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials_gsheet.json", SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def get_or_create_sheet(spreadsheet_name="Electricity Billing", sheet_name="Readings"):
    client = get_gsheet_client()
    if client is None:
        return None
    try:
        sh = client.open(spreadsheet_name)
    except gspread.SpreadsheetNotFound:
        sh = client.create(spreadsheet_name)
    try:
        worksheet = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=sheet_name, rows="100", cols="20")
        headers = [
            "Fecha", "Depto F - Lectura Anterior", "Depto F - Lectura Actual",
            "Depto G - Lectura Anterior", "Depto G - Lectura Actual",
            "Medidor General - Anterior", "Medidor General - Actual",
            "Consumo F (kWh)", "Consumo G (kWh)", "Total Consumo (kWh)",
            "Costo F ($)", "Costo G ($)", "Total Boleta ($)",
            "Notas"
        ]
        worksheet.append_row(headers)
    return worksheet

def save_reading(
    worksheet,
    f_previous, f_current,
    g_previous, g_current,
    general_previous, general_current,
    consumption_f, consumption_g, total_consumption,
    cost_f, cost_g, total_bill,
    notes=""
):
    if worksheet is None:
        return False
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        f_previous, f_current,
        g_previous, g_current,
        general_previous, general_current,
        consumption_f, consumption_g, total_consumption,
        cost_f, cost_g, total_bill,
        notes
    ]
    try:
        worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")
        return False

def get_last_readings(worksheet):
    if worksheet is None:
        return None
    try:
        records = worksheet.get_all_records()
        if not records:
            return None
        last = records[-1]
        return {
            "f_previous": last.get("Depto F - Lectura Anterior", 0),
            "f_current": last.get("Depto F - Lectura Actual", 0),
            "g_previous": last.get("Depto G - Lectura Anterior", 0),
            "g_current": last.get("Depto G - Lectura Actual", 0),
            "general_previous": last.get("Medidor General - Anterior", 0),
            "general_current": last.get("Medidor General - Actual", 0),
        }
    except Exception as e:
        st.error(f"Error reading from Google Sheets: {e}")
        return None

def get_history(worksheet, limit=20):
    if worksheet is None:
        return pd.DataFrame()
    try:
        records = worksheet.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        return df.tail(limit)
    except Exception as e:
        st.error(f"Error reading history: {e}")
        return pd.DataFrame()
