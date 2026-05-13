import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FILING_PROMPTS = {
    "employment": """
The taxpayer is filing an Individual Tax Return (ITR) for employment income.
Cover: Returns → File Return → Income Tax - Resident Individual →
Sheet F (employment income, enter gross pay, taxable pay, PAYE deducted, employer PIN) →
Sheet M (mortgage interest and insurance relief if applicable) →
Sheet T (tax computation, confirm personal relief of KES 28,800) →
Validate → Download ZIP → Upload ZIP → Submit → Download Acknowledgement Receipt.
""",
    "nil": """
The taxpayer is filing a Nil Return — they had no income this year.
Cover: Returns → File Return → Income Tax - Resident Individual →
Select correct year → Confirm all income fields are zero → Validate → Submit.
Reassure them nil returns are simple and take under 5 minutes.
Remind them the deadline is June 30 and late filing attracts a KES 2,000 penalty.
""",
    "business": """
The taxpayer is filing a Business / Self-Employment Income Tax Return.
Cover: Returns → File Return → Income Tax - Resident Individual →
Non-employment income section → Enter gross business income →
Enter allowable expenses → Net profit is calculated automatically →
Tax computation section → Enter withholding tax certificates as credits →
Validate → Download ZIP → Upload ZIP → Submit.
""",
    "rental": """
The taxpayer is filing a Monthly Rental Income (MRI) return.
Cover: Returns → File Return → Monthly Rental Income (MRI) →
Select correct year → Enter gross rent received (no deductions allowed) →
System calculates 7.5% tax automatically → Confirm and submit.
Remind them MRI has no deductions — tax is always 7.5% of gross rent.
""",
    "vat": """
The taxpayer is filing a VAT return for their business.
Cover: Returns → File Return → Value Added Tax → Select VAT period →
Enter output VAT from sales → Enter input VAT from purchases →
System calculates net VAT payable or refundable → Validate → Submit.
Remind them VAT returns are due by the 20th of the following month.
""",
    "turnover": """
The taxpayer is filing a Turnover Tax (TOT) return.
Cover: Returns → File Return → Turnover Tax → Select year →
Enter gross annual turnover → System calculates 1.5% TOT →
Deduct any instalment payments already made → Submit balance.
""",
    "capital_gains": """
The taxpayer is filing a Capital Gains Tax (CGT) return after selling an asset.
Cover: Returns → File Return → Capital Gains Tax →
Enter asset type and sale date → Enter sale price →
Enter original purchase cost → Enter incidental costs (legal fees, agent commissions) →
System calculates 5% CGT on net gain → Submit.
""",
    "company": """
The taxpayer is filing a Company Income Tax Return.
Cover: Returns → File Return → Income Tax - Resident Company →
Select financial year → Enter total revenue → Enter allowable expenses →
Net profit is calculated → 30% corporate tax applied →
Deduct instalment tax paid and withholding tax credits → Confirm balance → Submit.
""",
}


def generate_filing_guide(tax_summary):
    filing_type          = tax_summary.get("filing_type", "employment")
    filing_instructions  = FILING_PROMPTS.get(filing_type, FILING_PROMPTS["employment"])
    name                 = tax_summary.get("employee_name", "")
    greeting             = f"the taxpayer{' ' + name if name else ''}"

    prompt = f"""
You are a friendly KRA tax filing assistant for Kenyan taxpayers.
The taxpayer is already logged into iTax at itax.kra.go.ke.
Do NOT include a login step.

Filing Type: {tax_summary.get("filing_type_label", "Tax Return")}
Year of Income: {tax_summary.get("year", "2025")}
Taxpayer: {greeting}
Employer / Business: {tax_summary.get("employer_name") or "Not provided"}

Key Financial Figures to use in the guide:
- Gross Income / Revenue: KES {tax_summary.get("gross_pay", 0):,.2f}
- Benefits & Allowances: KES {tax_summary.get("benefits_allowances", 0):,.2f}
- Total Deductions: KES {tax_summary.get("total_deductions", 0):,.2f}
- Taxable Income: KES {tax_summary.get("taxable_pay", 0):,.2f}
- Tax on Income: KES {tax_summary.get("tax_on_income", 0):,.2f}
- Personal Relief: KES {tax_summary.get("personal_relief", 0):,.2f}
- Tax After Relief: KES {tax_summary.get("tax_after_relief", 0):,.2f}
- Tax Already Paid: KES {tax_summary.get("paye_deducted", 0):,.2f}
- Final Tax Balance: KES {tax_summary.get("tax_balance", 0):,.2f}
- Status: {tax_summary.get("status_message", "")}

Specific iTax steps to cover:
{filing_instructions}

FORMAT RULES — follow exactly:
- Use ONLY these HTML tags: <ol> <li> <h4> <p> <strong>
- Do NOT use markdown, asterisks, hashtags or **
- Use <strong> for field names and exact figures
- Structure EVERY step exactly like this:

<li>
  <h4>Short step title</h4>
  <p>Clear instruction. Enter <strong>KES 840,000</strong> in the <strong>Gross Pay</strong> field.</p>
</li>

- Use the EXACT figures from above wherever a number must be entered on iTax
- If a field is zero, instruct them to enter 0
- End with a single <p> paragraph summarising their tax position and what to expect after submission
- Tone: friendly, clear, reassuring. Write as if guiding a first-time filer.
{f'- Address the taxpayer by name ({name}) occasionally for a personal touch.' if name else ''}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"<p>Could not generate guide at this time. Error: {str(e)}</p>"


def generate_manual_guide(tax_summary):
    return generate_filing_guide(tax_summary)