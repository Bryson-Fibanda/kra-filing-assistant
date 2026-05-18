import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FILING_PROMPTS = {
    "employment": """
The taxpayer is filing an ITR for Employment Income Only on iTax.
They are already logged in. Walk them through these exact steps:

1. Returns menu → select "ITR For Employment Income Only"
2. On the e-Returns page:
   - Type is "Self"
   - Tax Obligation is "Income Tax - Resident"
   - Return Period From: 01/01/2025 (or the year they selected)
   - Return Period To: auto-populates as 31/12/2025
   - "Do you have Employment Income?" → select Yes
   - Click Next
3. Section A — Basic Information (this is the first section to fill):
   - Part 1: Answer these questions honestly:
     * "Has your employer provided you with a Car?" → Yes or No
     * "Do you have a Home Ownership Savings Plan?" → Yes or No (opens Section K if Yes)
     * "Do you earn any income from a foreign country?" → Yes or No
     * "Do you have a mortgage?" → Yes or No (opens Section J if Yes)
     * "Do you have a Life Insurance Policy?" → Yes or No (opens Section L if Yes)
     * "Have you been issued the Exemption Certificate for disability?" → Yes or No
   - Part 2 — Bank Details: Enter your bank name, branch, city/town and account number
     (KRA uses this if they owe you a refund)
   - Click Next
4. Section J — Mortgage (only if they answered Yes to mortgage in Section A):
   - Enter PIN of Lender (your bank's KRA PIN)
   - Enter Name of Lender (bank name)
   - Enter Mortgage Account Number
   - Enter Amount Borrowed (Ksh)
   - Enter Amount Outstanding at Year End (Ksh)
   - Enter Amount of Interest Paid (Ksh) — from your mortgage certificate
   - Click Add then Next
   - Note: Maximum mortgage interest allowed is KES 300,000
5. Section L — Insurance Relief (only if they answered Yes to insurance in Section A):
   - Enter PIN of Insurance Company
   - Enter Name of Insurance Company
   - Select Type of Policy: Life, Education, or Health
   - Enter Policy Holder (Self/Wife/Child)
   - Enter Commencement Date
   - Enter Maturity Date
   - Enter Sum Assured (Ksh)
   - Enter Annual Premium Paid (Ksh) — from your insurance certificate
   - Click Add then Next
   - Note: Insurance relief is 15% of premiums paid, maximum KES 60,000 per year
   - Applicable for Life, Health and Education insurance of 10 years and above
   - SHA contributions also qualify
6. Section F — Employment Income Details:
   - This section is ALREADY AUTO-POPULATED by iTax from your employer's P10 submissions
   - Verify the figures match your P9 form:
     * PIN of Employer — should match employer PIN on your P9
     * Gross Pay (Ksh) — verify against your P9
     * Total Employment Income (Ksh) — should match your P9 Taxable Pay
   - If figures match your P9 click Next
   - If figures do not match contact your employer — they may not have filed their P10
7. Section M — PAYE Details:
   - This section is ALSO AUTO-POPULATED by iTax
   - Verify the PAYE deducted figure matches your P9 PAYE Auto figure
   - If it matches click Next
   - If it does not match contact your employer
8. Section T — Tax Computation:
   - This section is FULLY AUTO-CALCULATED by iTax — you do not enter anything here
   - Review the figures and verify they match the expected values below:
     * Row 1: Total Deductions (Pension + higher of Mortgage or HOSP)
     * Row 2.1: Employment Income (from Section F)
     * Row 2.2: Disability Exemption (if applicable)
     * Row 2.3: Net Taxable Income
     * Row 2.4: Tax on Taxable Income
     * Row 2.5: Personal Relief (should show KES 28,800)
     * Row 2.6: Insurance Relief (from Section L)
     * Row 3.1: PAYE Deducted from Salary (from Section M)
     * Row 4: Tax Due / Refund Due — this is the final result
   - A negative figure means KRA owes you a refund — provide bank details in Section A
   - A positive figure means you owe KRA — pay via M-Pesa Paybill 572572
9. Confirm all details are accurate then click Submit
10. Download your Return Receipt / Acknowledgement
    (A survey will appear — you can skip it by clicking Not Now)
""",

    "nil": """
The taxpayer is filing a Nil Return — they had no income this year.
They are already logged in. Walk them through:

1. Returns menu → select "File Nil Return"
2. On the e-Returns page:
   - Tax Obligation: Income Tax - Resident
   - Return Period From: 01/01/2025
   - Return Period To: 31/12/2025
   - Click Next
3. Confirm the nil return declaration
4. All income fields will show zero — this is correct
5. Click Submit
6. Download the Acknowledgement Receipt
7. Check your registered email — a copy will be sent there

Reassure them nil returns are the simplest return type and take under 5 minutes.
Remind them the deadline is June 30 and late filing attracts a KES 2,000 flat penalty.
Even if they had no income, filing is mandatory if they have a KRA PIN.
""",

    "rental": """
The taxpayer is filing a Monthly Rental Income (MRI) return.
They are already logged in. Walk them through:

1. Returns menu → File Return → Monthly Rental Income (MRI)
2. Select the month and year they are filing for
   (MRI is filed monthly — one return per month)
3. Enter the property details:
   - Number of rental units
   - Gross rent received for that month (total from all units before any deductions)
4. iTax automatically calculates 7.5% tax on the gross rent
5. No deductions are allowed on MRI — tax is always 7.5% of gross rent received
6. Confirm the calculated tax figure
7. Validate then Submit
8. If tax is due pay via M-Pesa Paybill 572572 with their KRA PIN as account number
9. Download the acknowledgement receipt

Important reminders:
- MRI is filed monthly not annually
- Late filing penalty is 5% of tax due plus 1% interest per month
- Even if a property was vacant and no rent was collected a nil MRI return must be filed
- Annual gross rent must not exceed KES 15 million to qualify for MRI
""",

    "business": """
The taxpayer is filing a Business / Self-Employed Income Tax Return.
They are already logged in. Walk them through:

1. Returns menu → File Return → Income Tax - Resident Individual → select year of income
2. Select Yes to "Do you have Business Income?"
3. Section A — Basic Information:
   - Answer questions about insurance, mortgage, disability
   - Enter bank details for refunds if applicable
4. Business Income Section:
   - Enter Total Gross Business Income (all revenue for the year before expenses)
   - Enter Total Allowable Expenses:
     * Rent and rates
     * Salaries and wages paid to staff
     * Cost of goods and supplies purchased
     * Utilities (electricity, water, internet)
     * Other expenses directly related to earning the income
   - iTax calculates Net Profit = Gross Income minus Allowable Expenses
5. Important 2025 eTIMS requirement:
   - For any expense WITHOUT an eTIMS receipt you must:
     * Upload the original invoice or receipt to iTax
     * Prepare an Excel schedule listing all non-eTIMS expenses with supplier KRA PINs
   - Have these ready before you start filing
6. Withholding Tax Credits:
   - If clients deducted withholding tax before paying you enter the total here
   - You need your withholding tax certificates from those clients
   - These reduce your final tax payable
7. Instalment Tax Credits:
   - If you paid quarterly instalment tax during the year enter the total here
8. Section T — Tax Computation (auto-calculated):
   - Net Taxable Income = Net Profit
   - Tax applied at progressive bands (10%, 25%, 30%, 35%)
   - Less Personal Relief of KES 28,800
   - Less Withholding Tax Credits and Instalment Tax Credits
   - Final Tax Due or Refund Due
9. Validate → fix any errors → Submit → Download Receipt

Remind them:
- Keep all receipts and invoices — KRA may audit
- Expenses must be genuinely incurred to earn the income
- Late filing penalty is KES 2,000 or 5% of tax due whichever is higher
""",
}


def generate_filing_guide(tax_summary):
    filing_type         = tax_summary.get("filing_type", "employment")
    filing_instructions = FILING_PROMPTS.get(filing_type, FILING_PROMPTS["nil"])
    name                = tax_summary.get("employee_name", "")
    greeting            = f"the taxpayer{' ' + name if name else ''}"

    if filing_type == "employment":
        figures = f"""
FIGURES TO VERIFY ON iTax — from their P9 and calculations:

FROM P9 FORM (use these to verify Section F and Section M):
- Gross Pay: KES {tax_summary.get("gross_pay", 0):,.2f}
- Taxable Pay (verify against Section F Total Employment Income): KES {tax_summary.get("taxable_pay", 0):,.2f}
- Pension: KES {tax_summary.get("pension_contributions", 0):,.2f}
- PAYE Auto (verify against Section M): KES {tax_summary.get("paye_deducted", 0):,.2f}
- SHA Auto: KES {tax_summary.get("sha_contributions", 0):,.2f}
- NSSF Auto: KES {tax_summary.get("nssf_contributions", 0):,.2f}
- AHL Auto: KES {tax_summary.get("ahl_contributions", 0):,.2f}
- MPR Value: KES {tax_summary.get("mpr_value", 0):,.2f}
- Employer KRA PIN: {tax_summary.get("employer_pin") or "as shown on your P9"}

FROM iTax SCREENS (declare in Section A, details filled in Sections J and L):
- Mortgage Interest (Section J, cap KES 300,000): KES {tax_summary.get("mortgage_interest", 0):,.2f}
- Home Ownership Savings — HOSP (Section K, cap KES 96,000): KES {tax_summary.get("home_ownership_savings", 0):,.2f}
- Insurance Relief (Section L, 15% of premiums, max KES 60,000): KES {tax_summary.get("insurance_relief", 0):,.2f}
- Disability Exemption (Section T Row 2.2): KES {tax_summary.get("disability_exemption", 0):,.2f}

SECTION T — EXPECTED AUTO-CALCULATED VALUES (verify these match what iTax shows):
- Total Deductions (Row 1): KES {tax_summary.get("total_deductions", 0):,.2f}
- Employment Income (Row 2.1): KES {tax_summary.get("employment_income", 0):,.2f}
- Net Taxable Income (Row 2.3): KES {tax_summary.get("net_taxable_income", 0):,.2f}
- Tax on Income (Row 2.4): KES {tax_summary.get("tax_on_income", 0):,.2f}
- Personal Relief (Row 2.5): KES {tax_summary.get("personal_relief", 28800):,.2f}
- Tax After Reliefs: KES {tax_summary.get("tax_after_relief", 0):,.2f}
- PAYE Credits (Row 3.1): KES {tax_summary.get("paye_deducted", 0):,.2f}
- FINAL Tax Due / Refund Due (Row 4): KES {tax_summary.get("tax_balance", 0):,.2f}
- Status: {tax_summary.get("status_message", "")}
"""

    elif filing_type == "rental":
        figures = f"""
FIGURES FOR MRI RETURN:
- Number of Rental Units: {tax_summary.get("rental_units", 1)}
- Total Annual Gross Rent: KES {tax_summary.get("gross_pay", 0):,.2f}
- MRI Tax (7.5% of gross rent): KES {tax_summary.get("tax_on_income", 0):,.2f}
- MRI Tax Already Paid: KES {tax_summary.get("paye_deducted", 0):,.2f}
- Tax Balance Due / Refund: KES {tax_summary.get("tax_balance", 0):,.2f}
- Status: {tax_summary.get("status_message", "")}
Note: {tax_summary.get("tax_rate_note", "")}
"""

    elif filing_type == "business":
        figures = f"""
FIGURES FOR BUSINESS RETURN:
- Total Gross Business Income: KES {tax_summary.get("gross_pay", 0):,.2f}
- Total Allowable Expenses: KES {tax_summary.get("total_deductions", 0):,.2f}
- Net Profit (Taxable Income): KES {tax_summary.get("net_taxable_income", 0):,.2f}
- Tax on Net Profit: KES {tax_summary.get("tax_on_income", 0):,.2f}
- Personal Relief: KES {tax_summary.get("personal_relief", 28800):,.2f}
- Tax After Relief: KES {tax_summary.get("tax_after_relief", 0):,.2f}
- Withholding Tax Credits: KES {tax_summary.get("withholding_tax", 0):,.2f}
- Instalment Tax Credits: KES {tax_summary.get("instalment_tax", 0):,.2f}
- Total Tax Credits: KES {tax_summary.get("tax_credits", 0):,.2f}
- Final Tax Due / Refund Due: KES {tax_summary.get("tax_balance", 0):,.2f}
- Status: {tax_summary.get("status_message", "")}
"""

    else:
        figures = f"""
FIGURES:
- Status: {tax_summary.get("status_message", "")}
- Year: {tax_summary.get("year", "2025")}
"""

    prompt = f"""
You are a friendly KRA tax filing assistant for Kenyan taxpayers.
The taxpayer is already logged into iTax at itax.kra.go.ke.
Do NOT include a login step — start from the Returns menu.

Filing Type: {tax_summary.get("filing_type_label", "Tax Return")}
Year of Income: {tax_summary.get("year", "2025")}
Taxpayer: {greeting}
Employer / Business: {tax_summary.get("employer_name") or "Not provided"}

{figures}

Exact iTax steps to follow:
{filing_instructions}

FORMAT RULES — follow exactly, no exceptions:
- Use ONLY these HTML tags: <ol> <li> <h4> <p> <strong>
- Do NOT use markdown, asterisks, hashtags, or **
- Use <strong> for all section names, field names, and exact figures
- Structure EVERY step exactly like this:

<li>
  <h4>Step title here</h4>
  <p>Clear instruction. In <strong>Section F</strong>, verify that <strong>Total Employment Income</strong> shows <strong>KES 780,000</strong> — this should match your P9 Taxable Pay figure.</p>
</li>

- For fields that are AUTO-POPULATED by iTax: tell the user to verify the figure matches their P9
- For fields the user must fill in themselves: tell them exactly what to enter
- For sections that are zero or not applicable: tell them to skip or leave as 0
- End with ONE <p> paragraph summarising their tax position and what to expect after submission
- Tone: friendly, clear, reassuring. Write as if guiding a first-time filer.
{f'- Use the name {name} occasionally to make it personal.' if name else ''}
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
