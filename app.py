import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)

import os
import uuid
import bleach
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from groq import Groq as GroqClient
from utils.pdf_extractor import extract_p9_data, manual_entry_defaults
from utils.tax_calculator import calculate_tax
from utils.guide_generator import generate_filing_guide

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

csrf = CSRFProtect(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

groq_client = GroqClient(api_key=os.getenv("GROQ_API_KEY"))

FILING_TYPE_LABELS = {
    "employment": "Employment Income (P9)",
    "nil":        "Nil Return",
    "rental":     "Rental Income (MRI)",
    "business":   "Business / Self-Employed",
}

HELP_SYSTEM_PROMPT = """
You are a friendly and knowledgeable KRA (Kenya Revenue Authority) help assistant.
You help Kenyan taxpayers navigate KRA services on iTax (itax.kra.go.ke).

You can help with:
- How to register for a KRA PIN for the first time
- What a KRA PIN looks like and how to read it
  (Individual PIN example: A012345678B — letter, 9 digits, letter)
  (Company PIN example: P051234567A — starts with P)
- How to get a Tax Compliance Certificate (TCC)
- How to register for eTIMS (electronic invoicing for businesses)
- How to reset an iTax password
- How to update personal details on iTax (phone, email, address)
- What to do when a KRA PIN is blocked or suspended
- How to check tax balance or outstanding taxes on iTax
- How to register for VAT in Kenya
- How to apply for a tax refund from KRA
- How to object to a KRA tax assessment
- Late filing penalties and how to still file after the deadline
- General iTax navigation questions
- KRA deadlines and important dates

Always:
- Give clear numbered step by step instructions
- Be friendly and reassuring
- Use plain simple English
- Format responses using ONLY: <p> <ol> <ul> <li> <strong>
- Do NOT use markdown, asterisks, or hashtags
"""

ALLOWED_HTML_TAGS = ['p', 'ol', 'ul', 'li', 'h4', 'strong']
ALLOWED_HTML_ATTRS = {}


def sanitize_html(raw):
    return bleach.clean(raw, tags=ALLOWED_HTML_TAGS, attributes=ALLOWED_HTML_ATTRS)


def sanitize_text(value):
    return bleach.clean(str(value), tags=[], strip=True).strip()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_form_data(req, filing_type):
    def num(field, default=0.0):
        val = req.form.get(field, default)
        try:
            return float(val) if val != "" else default
        except (ValueError, TypeError):
            return default

    def txt(field):
        return sanitize_text(req.form.get(field, ""))

    base = manual_entry_defaults()
    base["filing_type"]       = sanitize_text(filing_type)
    base["filing_type_label"] = FILING_TYPE_LABELS.get(filing_type, filing_type)
    base["employee_name"]     = txt("employee_name")
    base["employer_name"]     = txt("employer_name")
    base["employer_pin"]      = txt("employer_pin")
    base["year"]              = txt("year")

    if filing_type == "employment":
        base["gross_pay"]               = num("gross_pay")
        base["taxable_pay"]             = num("taxable_pay")
        base["pension_contributions"]   = num("pension_contributions")
        base["paye_deducted"]           = num("paye_deducted")
        base["sha_contributions"]       = num("sha_contributions")
        base["nssf_contributions"]      = num("nssf_contributions")
        base["ahl_contributions"]       = num("ahl_contributions")
        base["mpr_value"]               = num("mpr_value")
        base["owner_occupied_interest"] = num("owner_occupied_interest")
        base["home_ownership_savings"]  = num("home_ownership_savings")
        base["insurance_relief"]        = num("insurance_relief")
        base["disability_exemption"]    = num("disability_exemption")

    elif filing_type == "nil":
        base["nil_reason"] = txt("nil_reason")

    elif filing_type == "rental":
        base["gross_pay"]     = num("gross_pay")
        base["paye_deducted"] = num("paye_deducted")
        base["rental_units"]  = int(num("rental_units", 1))

    elif filing_type == "business":
        base["gross_pay"]        = num("gross_pay")
        base["business_expenses"] = num("business_expenses")
        base["withholding_tax"]  = num("withholding_tax")
        base["instalment_tax"]   = num("instalment_tax")

    return base


# ─── Security Headers ───
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    return response


# ─── Main Routes ───
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    filing_type = sanitize_text(request.form.get("filing_type", "employment"))

    if filing_type not in FILING_TYPE_LABELS:
        flash("Invalid filing type selected.", "error")
        return redirect(url_for("index"))

    extracted_data = get_form_data(request, filing_type)
    tax_summary    = calculate_tax(extracted_data)
    filing_guide   = generate_filing_guide(tax_summary)
    filing_guide   = sanitize_html(filing_guide)

    session["tax_summary"]  = tax_summary
    session["filing_guide"] = filing_guide

    return redirect(url_for("results"))


@app.route("/results")
def results():
    tax_summary  = session.get("tax_summary")
    filing_guide = session.get("filing_guide")

    if not tax_summary:
        flash("No results found. Please start a new return.", "error")
        return redirect(url_for("index"))

    return render_template("results.html",
                           tax_summary=tax_summary,
                           filing_guide=filing_guide)


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))


# ─── Help Bot ───
@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/help/chat", methods=["POST"])
@csrf.exempt
def help_chat():
    try:
        data     = request.get_json()
        messages = data.get("messages", [])

        clean_messages = []
        for m in messages[-10:]:
            if isinstance(m, dict) and m.get("role") in ["user", "assistant"]:
                clean_messages.append({
                    "role": m["role"],
                    "content": sanitize_text(m.get("content", ""))
                })

        full_messages = [{"role": "system", "content": HELP_SYSTEM_PROMPT}] + clean_messages

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=full_messages,
            max_tokens=1000
        )

        reply = sanitize_html(response.choices[0].message.content)
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": "Something went wrong. Please try again."}), 500


# ─── Other Pages ───
@app.route("/checklist")
def checklist():
    return render_template("checklist.html")


@app.route("/fileforme")
def fileforme():
    return render_template("fileforme.html")


@app.route("/translate-guide", methods=["POST"])
@csrf.exempt
def translate_guide():
    try:
        data  = request.get_json()
        guide = sanitize_text(data.get("guide", ""))

        prompt = f"""
Translate the following KRA iTax filing guide into Swahili.
Keep all HTML tags exactly as they are.
Only translate the text content inside the tags.
Keep all KES amounts, figures, field names, and iTax menu names in English.
Do NOT add extra text or markdown.

Guide:
{guide}
"""
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )

        translated = sanitize_html(response.choices[0].message.content)
        return jsonify({"translated": translated})

    except Exception as e:
        return jsonify({"error": "Translation failed. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
