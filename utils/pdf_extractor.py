import pdfplumber
import re


def extract_p9_data(pdf_path):
    extracted = {
        "employee_name": None,
        "employer_name": None,
        "employer_pin": None,
        "year": None,
        "gross_pay": 0.0,
        "taxable_pay": 0.0,
        "pension_contributions": 0.0,
        "paye_deducted": 0.0,
        "sha_contributions": 0.0,
        "nssf_contributions": 0.0,
        "ahl_contributions": 0.0,
        "mpr_value": 0.0,
        "owner_occupied_interest": 0.0,
        "home_ownership_savings": 0.0,
        "insurance_relief": 0.0,
        "disability_exemption": 0.0,
    }

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    def find_amount(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(",", "").strip()
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    name_match = re.search(r"Employee\s*Name[:\s]+([A-Za-z\s]+)", full_text, re.IGNORECASE)
    if name_match:
        extracted["employee_name"] = name_match.group(1).strip()

    employer_match = re.search(r"Employer\s*Name[:\s]+([A-Za-z\s&]+)", full_text, re.IGNORECASE)
    if employer_match:
        extracted["employer_name"] = employer_match.group(1).strip()

    employer_pin_match = re.search(r"Employer\s*PIN[:\s]+([A-Z0-9]+)", full_text, re.IGNORECASE)
    if employer_pin_match:
        extracted["employer_pin"] = employer_pin_match.group(1).strip()

    year_match = re.search(r"Year\s*of\s*Income[:\s]+(\d{4})", full_text, re.IGNORECASE)
    if year_match:
        extracted["year"] = year_match.group(1).strip()

    extracted["gross_pay"] = find_amount(r"Gross\s*(?:Pay|Salary)[:\s]+([\d,]+\.?\d*)", full_text)
    extracted["taxable_pay"] = find_amount(r"Taxable\s*Pay[:\s]+([\d,]+\.?\d*)", full_text)
    extracted["pension_contributions"] = find_amount(r"Pension[:\s]+([\d,]+\.?\d*)", full_text)
    extracted["paye_deducted"] = find_amount(r"PAYE\s*Auto[:\s]+([\d,]+\.?\d*)", full_text)
    extracted["sha_contributions"] = find_amount(r"SHA\s*Auto[:\s]+([\d,]+\.?\d*)", full_text)
    extracted["nssf_contributions"] = find_amount(r"NSSF\s*Auto[:\s]+([\d,]+\.?\d*)", full_text)
    extracted["ahl_contributions"] = find_amount(r"AHL\s*Auto[:\s]+([\d,]+\.?\d*)", full_text)
    extracted["mpr_value"] = find_amount(r"MPR\s*Value[:\s]+([\d,]+\.?\d*)", full_text)

    return extracted


def manual_entry_defaults():
    return {
        "employee_name": "",
        "employer_name": "",
        "employer_pin": "",
        "year": "2025",
        "gross_pay": 0.0,
        "taxable_pay": 0.0,
        "pension_contributions": 0.0,
        "paye_deducted": 0.0,
        "sha_contributions": 0.0,
        "nssf_contributions": 0.0,
        "ahl_contributions": 0.0,
        "mpr_value": 0.0,
        "owner_occupied_interest": 0.0,
        "home_ownership_savings": 0.0,
        "insurance_relief": 0.0,
        "disability_exemption": 0.0,
        "business_expenses": 0.0,
        "withholding_tax": 0.0,
        "instalment_tax": 0.0,
        "rental_units": 1,
        "nil_reason": "unemployed",
    }
