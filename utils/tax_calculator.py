def calculate_tax(data):
    filing_type = data.get("filing_type", "employment")
    if filing_type == "employment":
        return _employment_tax(data)
    elif filing_type == "nil":
        return _nil_return(data)
    elif filing_type == "rental":
        return _rental_tax(data)
    elif filing_type == "business":
        return _business_tax(data)
    else:
        return _nil_return(data)


# ─────────────────────────────────────────
# EMPLOYMENT — Matches iTax Section T exactly
# ─────────────────────────────────────────
def _employment_tax(data):
    # ── From P9 form ──
    taxable_pay   = float(data.get("taxable_pay", 0))
    pension       = float(data.get("pension_contributions", 0))
    paye_deducted = float(data.get("paye_deducted", 0))
    sha           = float(data.get("sha_contributions", 0))
    nssf          = float(data.get("nssf_contributions", 0))
    ahl           = float(data.get("ahl_contributions", 0))
    mpr_value     = float(data.get("mpr_value", 0))
    gross_pay     = float(data.get("gross_pay", 0))

    # ── From iTax screens (user enters if applicable) ──
    mortgage_interest = float(data.get("owner_occupied_interest", 0))
    home_savings      = float(data.get("home_ownership_savings", 0))
    insurance_relief  = float(data.get("insurance_relief", 0))
    disability_exempt = float(data.get("disability_exemption", 0))

    # ── iTax Caps ──
    pension           = min(pension, 360000)     # KES 30,000/month cap
    mortgage_interest = min(mortgage_interest, 300000)  # iTax Section T cap
    home_savings      = min(home_savings, 96000)         # iTax Section T cap
    insurance_relief  = min(insurance_relief, 60000)     # Sheet L cap

    # ── Section T Row 1: Total Deductions ──
    # Pension + Higher of (Mortgage Interest OR Home Ownership Savings Plan)
    higher_of_mortgage_or_home = max(mortgage_interest, home_savings)
    total_deductions = pension + higher_of_mortgage_or_home

    # ── Section T Row 2.1: Employment Income ──
    # Comes from Sheet F — Total Taxable Employment Income = Taxable Pay on P9
    employment_income = taxable_pay

    # ── Section T Row 2.2: Disability Exemption ──
    disability_exempt = min(disability_exempt, employment_income)

    # ── Section T Row 2.3: Net Taxable Income ──
    # Employment Income minus Total Deductions minus Disability Exemption
    net_taxable_income = max(employment_income - total_deductions - disability_exempt, 0)

    # ── Section T Row 2.4: Tax on Taxable Income ──
    tax_on_income = _apply_bands(net_taxable_income)

    # ── Section T Reliefs ──
    personal_relief = 28800.0  # Fixed KES 28,800/year — auto-filled by iTax

    # ── Section T: Tax Payable after Reliefs ──
    tax_after_relief = max(tax_on_income - personal_relief - insurance_relief, 0)

    # ── Section T Row 3: Tax Credits ──
    # 3.1 PAYE Deducted from Salary (Sheet M)
    # 3.2 Instalment Tax Paid in Advance (0 for most employees)
    # 3.3 Credits u/s 41 DTAA (0 for most employees)
    tax_credits = paye_deducted

    # ── Section T Final: Tax Due / Refund Due ──
    tax_balance = tax_after_relief - tax_credits

    return _build_summary(data, {
        "gross_pay":                   gross_pay,
        "taxable_pay":                 taxable_pay,
        "employment_income":           employment_income,
        "pension_contributions":       pension,
        "sha_contributions":           sha,
        "nssf_contributions":          nssf,
        "ahl_contributions":           ahl,
        "mpr_value":                   mpr_value,
        "mortgage_interest":           mortgage_interest,
        "home_ownership_savings":      home_savings,
        "higher_of_mortgage_or_home":  higher_of_mortgage_or_home,
        "total_deductions":            total_deductions,
        "disability_exemption":        disability_exempt,
        "net_taxable_income":          net_taxable_income,
        "tax_on_income":               tax_on_income,
        "personal_relief":             personal_relief,
        "insurance_relief":            insurance_relief,
        "tax_after_relief":            tax_after_relief,
        "paye_deducted":               paye_deducted,
        "tax_credits":                 tax_credits,
        "tax_balance":                 tax_balance,
        "benefits_allowances":         0,
        "total_gross":                 gross_pay,
    })


# ─────────────────────────────────────────
# NIL RETURN
# ─────────────────────────────────────────
def _nil_return(data):
    return _build_summary(data, {
        "gross_pay":        0,
        "taxable_pay":      0,
        "tax_on_income":    0,
        "personal_relief":  0,
        "tax_after_relief": 0,
        "paye_deducted":    0,
        "tax_credits":      0,
        "tax_balance":      0,
        "nil_reason":       data.get("nil_reason", "unemployed"),
    })


# ─────────────────────────────────────────
# RENTAL INCOME (MRI) — Flat 7.5%
# ─────────────────────────────────────────
def _rental_tax(data):
    gross_rent   = float(data.get("gross_pay", 0))
    tax_paid     = float(data.get("paye_deducted", 0))
    rental_units = int(data.get("rental_units", 1))

    # MRI: 7.5% on gross rent — no deductions allowed
    tax_on_income = round(gross_rent * 0.075, 2)
    tax_balance   = tax_on_income - tax_paid

    return _build_summary(data, {
        "gross_pay":        gross_rent,
        "total_gross":      gross_rent,
        "taxable_pay":      gross_rent,
        "tax_on_income":    tax_on_income,
        "personal_relief":  0,
        "tax_after_relief": tax_on_income,
        "paye_deducted":    tax_paid,
        "tax_credits":      tax_paid,
        "tax_balance":      tax_balance,
        "rental_units":     rental_units,
        "tax_rate_note":    "MRI is taxed at a flat rate of 7.5% on gross rent. No deductions are allowed.",
    })


# ─────────────────────────────────────────
# BUSINESS / SELF-EMPLOYED
# ─────────────────────────────────────────
def _business_tax(data):
    gross_income     = float(data.get("gross_pay", 0))
    expenses         = float(data.get("business_expenses", 0))
    withholding_tax  = float(data.get("withholding_tax", 0))
    instalment_tax   = float(data.get("instalment_tax", 0))
    personal_relief  = 28800.0

    # Net profit = Gross Income minus Allowable Deductions
    net_profit       = max(gross_income - expenses, 0)
    tax_on_income    = _apply_bands(net_profit)
    tax_after_relief = max(tax_on_income - personal_relief, 0)

    # Total credits = Withholding Tax + Instalment Tax paid
    tax_credits  = withholding_tax + instalment_tax
    tax_balance  = tax_after_relief - tax_credits

    return _build_summary(data, {
        "gross_pay":        gross_income,
        "total_gross":      gross_income,
        "total_deductions": expenses,
        "taxable_pay":      net_profit,
        "net_taxable_income": net_profit,
        "tax_on_income":    tax_on_income,
        "personal_relief":  personal_relief,
        "tax_after_relief": tax_after_relief,
        "withholding_tax":  withholding_tax,
        "instalment_tax":   instalment_tax,
        "paye_deducted":    withholding_tax,
        "tax_credits":      tax_credits,
        "tax_balance":      tax_balance,
        "tax_rate_note":    "Business income taxed on net profit using progressive KRA bands.",
    })


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def _apply_bands(taxable_income):
    """KRA 2025 progressive tax bands."""
    bands = [
        (288000,       0.10),
        (100000,       0.25),
        (5612000,      0.30),
        (float("inf"), 0.35),
    ]
    tax = 0.0
    remaining = taxable_income
    for limit, rate in bands:
        if remaining <= 0:
            break
        chunk = min(remaining, limit)
        tax += chunk * rate
        remaining -= chunk
    return round(tax, 2)


def _build_summary(data, computed):
    tax_balance = computed.get("tax_balance", 0)

    if abs(tax_balance) < 1:
        status         = "balanced"
        status_message = "Your tax is fully settled. You owe KRA nothing."
        status_color   = "green"
    elif tax_balance > 0:
        status         = "payable"
        status_message = f"You have a tax balance of KES {tax_balance:,.2f} payable to KRA."
        status_color   = "red"
    else:
        status         = "refund"
        status_message = f"KRA owes you a refund of KES {abs(tax_balance):,.2f}."
        status_color   = "yellow"

    if data.get("filing_type") == "nil":
        status         = "balanced"
        status_message = "Nil return — no tax due. Just submit before June 30."
        status_color   = "green"

    summary = {
        "filing_type":               data.get("filing_type", "employment"),
        "filing_type_label":         data.get("filing_type_label", "Tax Return"),
        "employee_name":             data.get("employee_name", ""),
        "employee_pin":              data.get("employee_pin", ""),
        "employer_name":             data.get("employer_name", ""),
        "employer_pin":              data.get("employer_pin", ""),
        "year":                      data.get("year", "2025"),
        "gross_pay":                 0,
        "benefits_allowances":       0,
        "total_gross":               0,
        "taxable_pay":               0,
        "employment_income":         0,
        "pension_contributions":     0,
        "sha_contributions":         0,
        "nssf_contributions":        0,
        "ahl_contributions":         0,
        "mpr_value":                 0,
        "mortgage_interest":         0,
        "home_ownership_savings":    0,
        "higher_of_mortgage_or_home": 0,
        "total_deductions":          0,
        "disability_exemption":      0,
        "net_taxable_income":        0,
        "tax_on_income":             0,
        "personal_relief":           0,
        "insurance_relief":          0,
        "tax_after_relief":          0,
        "paye_deducted":             0,
        "withholding_tax":           0,
        "instalment_tax":            0,
        "tax_credits":               0,
        "tax_balance":               0,
        "rental_units":              1,
        "tax_rate_note":             "",
        "nil_reason":                "",
        "status":                    status,
        "status_message":            status_message,
        "status_color":              status_color,
    }

    summary.update(computed)
    return summary
