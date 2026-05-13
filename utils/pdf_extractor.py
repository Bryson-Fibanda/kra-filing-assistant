import pdfplumber
import re

def extract_p9_data(pdf_path):
    """
    Extracts all key figures from a KRA P9 PDF.
    Returns a dictionary of extracted values.
    """
    extracted = {
        "employee_name": None,
        "employee_pin": None,
        "employer_name": None,
        "employer_pin": None,
        "year": None,
        "gross_pay": 0.0,
        "benefits_allowances": 0.0,
        "pension_contributions": 0.0,
        "shif_contributions": 0.0,
        "ahl_contributions": 0.0,
        "prmf_contributions": 0.0,
        "insurance_relief": 0.0,
        "owner_occupied_interest": 0.0,
        "paye_deducted": 0.0,
        "taxable_pay": 0.0,
        "personal_relief": 28800.0,  # Fixed by KRA for 2024
    }

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        # Extract tables for numeric data
        all_tables = []
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                all_tables.extend(tables)

    # --- Extract employee/employer info ---
    name_match = re.search(r"Employee\s*Name[:\s]+([A-Za-z\s]+)", full_text, re.IGNORECASE)
    if name_match:
        extracted["employee_name"] = name_match.group(1).strip()

    pin_match = re.search(r"Employee\s*PIN[:\s]+([A-Z0-9]+)", full_text, re.IGNORECASE)
    if pin_match:
        extracted["employee_pin"] = pin_match.group(1).strip()

    employer_match = re.search(r"Employer\s*Name[:\s]+([A-Za-z\s&]+)", full_text, re.IGNORECASE)
    if employer_match:
        extracted["employer_name"] = employer_match.group(1).strip()

    employer_pin_match = re.search(r"Employer\s*PIN[:\s]+([A-Z0-9]+)", full_text, re.IGNORECASE)
    if employer_pin_match:
        extracted["employer_pin"] = employer_pin_match.group(1).strip()

    year_match = re.search(r"Year\s*of\s*Income[:\s]+(\d{4})", full_text, re.IGNORECASE)
    if year_match:
        extracted["year"] = year_match.group(1).strip()

    # --- Helper to find numeric values ---
    def find_amount(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(",", "").strip()
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    # --- Extract key financial figures ---
    extracted["gross_pay"] = find_amount(
        r"Gross\s*(?:Pay|Salary)[:\s]+([\d,]+\.?\d*)", full_text)

    extracted["benefits_allowances"] = find_amount(
        r"(?:Benefits|Allowances)[:\s]+([\d,]+\.?\d*)", full_text)

    extracted["taxable_pay"] = find_amount(
        r"Taxable\s*Pay[:\s]+([\d,]+\.?\d*)", full_text)

    extracted["paye_deducted"] = find_amount(
        r"PAYE\s*(?:Deducted|Tax)[:\s]+([\d,]+\.?\d*)", full_text)

    extracted["pension_contributions"] = find_amount(
        r"(?:Pension|Retirement\s*Scheme)[:\s]+([\d,]+\.?\d*)", full_text)

    extracted["shif_contributions"] = find_amount(
        r"SHIF[:\s]+([\d,]+\.?\d*)", full_text)

    extracted["ahl_contributions"] = find_amount(
        r"(?:AHL|Affordable\s*Housing)[:\s]+([\d,]+\.?\d*)", full_text)

    extracted["prmf_contributions"] = find_amount(
        r"(?:PRMF|Post\s*Retirement\s*Medical)[:\s]+([\d,]+\.?\d*)", full_text)

    extracted["insurance_relief"] = find_amount(
        r"Insurance\s*Relief[:\s]+([\d,]+\.?\d*)", full_text)

    extracted["owner_occupied_interest"] = find_amount(
        r"(?:Owner\s*Occupied|Mortgage)\s*Interest[:\s]+([\d,]+\.?\d*)", full_text)

    # --- Fallback: scan tables if regex missed key figures ---
    if extracted["gross_pay"] == 0.0 and all_tables:
        for table in all_tables:
            for row in table:
                if row:
                    row_text = " ".join([str(cell) for cell in row if cell])
                    if "gross" in row_text.lower():
                        for cell in reversed(row):
                            if cell:
                                clean = str(cell).replace(",", "").strip()
                                try:
                                    extracted["gross_pay"] = float(clean)
                                    break
                                except ValueError:
                                    continue

    return extracted


def manual_entry_defaults():
    """Returns empty structure for manual entry fallback."""
    return {
        "employee_name": "",
        "employee_pin": "",
        "employer_name": "",
        "employer_pin": "",
        "year": "2024",
        "gross_pay": 0.0,
        "benefits_allowances": 0.0,
        "pension_contributions": 0.0,
        "shif_contributions": 0.0,
        "ahl_contributions": 0.0,
        "prmf_contributions": 0.0,
        "insurance_relief": 0.0,
        "owner_occupied_interest": 0.0,
        "paye_deducted": 0.0,
        "taxable_pay": 0.0,
        "personal_relief": 28800.0,
    }