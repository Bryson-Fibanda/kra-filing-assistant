def calculate_tax(data):
    """
    Routes to the correct calculator based on filing type.
    Returns a unified tax summary dictionary.
    """
    filing_type = data.get("filing_type", "employment")

    if filing_type == "employment":
        return _employment_tax(data)
    elif filing_type == "nil":
        return _nil_return(data)
    elif filing_type == "business":
        return _business_tax(data)
    elif filing_type == "rental":
        return _rental_tax(data)
    elif filing_type == "vat":
        return _vat_return(data)
    elif filing_type == "turnover":
        return _turnover_tax(data)
    elif filing_type == "capital_gains":
        return _capital_gains_tax(data)
    elif filing_type == "company":
        return _company_tax(data)
    else:
        return _employment_tax(data)


# ─────────────────────────────────────────
# EMPLOYMENT INCOME (P9)
# ─────────────────────────────────────────
def _employment_tax(data):
    gross_pay      = float(data.get("gross_pay", 0))
    benefits       = float(data.get("benefits_allowances", 0))
    pension        = float(data.get("pension_contributions", 0))
    shif           = float(data.get("shif_contributions", 0))
    ahl            = float(data.get("ahl_contributions", 0))
    prmf           = float(data.get("prmf_contributions", 0))
    mortgage       = float(data.get("owner_occupied_interest", 0))
    ins_relief     = float(data.get("insurance_relief", 0))
    paye_deducted  = float(data.get("paye_deducted", 0))
    personal_relief = 28800.0

    # Caps — 2024/2025 rules
    pension  = min(pension, 360000)
    mortgage = min(mortgage, 360000)
    prmf     = min(prmf, 180000)
    ins_relief = min(ins_relief, 60000)

    total_gross      = gross_pay + benefits
    total_deductions = pension + mortgage + shif + ahl + prmf
    taxable_pay      = max(total_gross - total_deductions, 0)
    tax_on_income    = _apply_bands(taxable_pay)
    total_relief     = personal_relief + ins_relief
    tax_after_relief = max(tax_on_income - total_relief, 0)
    tax_balance      = tax_after_relief - paye_deducted

    return _build_summary(data, {
        "gross_pay":            gross_pay,
        "benefits_allowances":  benefits,
        "total_gross":          total_gross,
        "pension_contributions":pension,
        "shif_contributions":   shif,
        "ahl_contributions":    ahl,
        "prmf_contributions":   prmf,
        "mortgage_interest":    mortgage,
        "total_deductions":     total_deductions,
        "taxable_pay":          taxable_pay,
        "tax_on_income":        tax_on_income,
        "personal_relief":      personal_relief,
        "insurance_relief":     ins_relief,
        "total_relief":         total_relief,
        "tax_after_relief":     tax_after_relief,
        "paye_deducted":        paye_deducted,
        "tax_balance":          tax_balance,
    })


# ─────────────────────────────────────────
# NIL RETURN
# ─────────────────────────────────────────
def _nil_return(data):
    return _build_summary(data, {
        "gross_pay":       0,
        "taxable_pay":     0,
        "tax_on_income":   0,
        "personal_relief": 0,
        "tax_after_relief":0,
        "paye_deducted":   0,
        "tax_balance":     0,
        "nil_reason":      data.get("nil_reason", "unemployed"),
    })


# ─────────────────────────────────────────
# BUSINESS / SELF-EMPLOYED
# ─────────────────────────────────────────
def _business_tax(data):
    gross_income   = float(data.get("gross_pay", 0))
    expenses       = float(data.get("business_expenses", 0))
    withholding    = float(data.get("paye_deducted", 0))
    personal_relief = 28800.0

    net_profit       = max(gross_income - expenses, 0)
    tax_on_income    = _apply_bands(net_profit)
    tax_after_relief = max(tax_on_income - personal_relief, 0)
    tax_balance      = tax_after_relief - withholding

    return _build_summary(data, {
        "gross_pay":        gross_income,
        "total_gross":      gross_income,
        "total_deductions": expenses,
        "taxable_pay":      net_profit,
        "tax_on_income":    tax_on_income,
        "personal_relief":  personal_relief,
        "tax_after_relief": tax_after_relief,
        "paye_deducted":    withholding,
        "tax_balance":      tax_balance,
    })


# ─────────────────────────────────────────
# RENTAL INCOME (MRI) — 7.5% flat rate
# ─────────────────────────────────────────
def _rental_tax(data):
    gross_rent    = float(data.get("gross_pay", 0))
    tax_paid      = float(data.get("paye_deducted", 0))
    rental_units  = int(data.get("rental_units", 1))

    # MRI: 7.5% on gross rent, no deductions allowed
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
        "tax_balance":      tax_balance,
        "rental_units":     rental_units,
        "tax_rate_note":    "MRI taxed at flat 7.5% on gross rent — no deductions allowed",
    })


# ─────────────────────────────────────────
# VAT — 16% standard rate
# ─────────────────────────────────────────
def _vat_return(data):
    output_vat = float(data.get("gross_pay", 0))
    input_vat  = float(data.get("paye_deducted", 0))
    tax_balance = output_vat - input_vat

    return _build_summary(data, {
        "gross_pay":        output_vat,
        "taxable_pay":      output_vat,
        "tax_on_income":    output_vat,
        "personal_relief":  input_vat,
        "tax_after_relief": max(tax_balance, 0),
        "paye_deducted":    input_vat,
        "tax_balance":      tax_balance,
        "vat_month":        data.get("vat_month", ""),
        "tax_rate_note":    "VAT balance = Output VAT minus Input VAT",
    })


# ─────────────────────────────────────────
# TURNOVER TAX (TOT) — 1.5% of gross turnover
# ─────────────────────────────────────────
def _turnover_tax(data):
    turnover    = float(data.get("gross_pay", 0))
    tot_paid    = float(data.get("paye_deducted", 0))

    tax_on_income = round(turnover * 0.015, 2)
    tax_balance   = tax_on_income - tot_paid

    return _build_summary(data, {
        "gross_pay":        turnover,
        "total_gross":      turnover,
        "taxable_pay":      turnover,
        "tax_on_income":    tax_on_income,
        "personal_relief":  0,
        "tax_after_relief": tax_on_income,
        "paye_deducted":    tot_paid,
        "tax_balance":      tax_balance,
        "tax_rate_note":    "TOT charged at 1.5% of gross annual turnover",
    })


# ─────────────────────────────────────────
# CAPITAL GAINS TAX — 5% of net gain
# ─────────────────────────────────────────
def _capital_gains_tax(data):
    sale_price       = float(data.get("gross_pay", 0))
    purchase_cost    = float(data.get("business_expenses", 0))
    incidental_costs = float(data.get("owner_occupied_interest", 0))
    cgt_paid         = float(data.get("paye_deducted", 0))

    net_gain      = max(sale_price - purchase_cost - incidental_costs, 0)
    tax_on_income = round(net_gain * 0.05, 2)
    tax_balance   = tax_on_income - cgt_paid

    return _build_summary(data, {
        "gross_pay":        sale_price,
        "total_gross":      sale_price,
        "total_deductions": purchase_cost + incidental_costs,
        "taxable_pay":      net_gain,
        "tax_on_income":    tax_on_income,
        "personal_relief":  0,
        "tax_after_relief": tax_on_income,
        "paye_deducted":    cgt_paid,
        "tax_balance":      tax_balance,
        "asset_type":       data.get("asset_type", "property"),
        "tax_rate_note":    "CGT charged at 5% on net gain (sale price minus cost minus expenses)",
    })


# ─────────────────────────────────────────
# COMPANY RETURN — 30% corporate tax
# ─────────────────────────────────────────
def _company_tax(data):
    revenue          = float(data.get("gross_pay", 0))
    expenses         = float(data.get("business_expenses", 0))
    instalment_paid  = float(data.get("paye_deducted", 0))
    withholding_tax  = float(data.get("insurance_relief", 0))

    net_profit       = max(revenue - expenses, 0)
    tax_on_income    = round(net_profit * 0.30, 2)
    total_credits    = instalment_paid + withholding_tax
    tax_balance      = tax_on_income - total_credits

    return _build_summary(data, {
        "gross_pay":        revenue,
        "total_gross":      revenue,
        "total_deductions": expenses,
        "taxable_pay":      net_profit,
        "tax_on_income":    tax_on_income,
        "personal_relief":  0,
        "insurance_relief": withholding_tax,
        "tax_after_relief": max(tax_on_income - withholding_tax, 0),
        "paye_deducted":    instalment_paid,
        "tax_balance":      tax_balance,
        "tax_rate_note":    "Corporate tax charged at 30% on net profit",
    })


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def _apply_bands(taxable_income):
    """KRA 2024/2025 progressive tax bands."""
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
    """Merges form data with computed values and sets status."""
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

    # Special case for nil returns
    if data.get("filing_type") == "nil":
        status         = "balanced"
        status_message = "Nil return — no tax due. Just submit your return before June 30."
        status_color   = "green"

    summary = {
        # Identity
        "filing_type":       data.get("filing_type", "employment"),
        "filing_type_label": data.get("filing_type_label", "Tax Return"),
        "employee_name":     data.get("employee_name", ""),
        "employee_pin":      data.get("employee_pin", ""),
        "employer_name":     data.get("employer_name", ""),
        "employer_pin":      data.get("employer_pin", ""),
        "year":              data.get("year", "2025"),

        # Defaults — overridden by computed
        "gross_pay":             0,
        "benefits_allowances":   0,
        "total_gross":           0,
        "pension_contributions": 0,
        "shif_contributions":    0,
        "ahl_contributions":     0,
        "prmf_contributions":    0,
        "mortgage_interest":     0,
        "total_deductions":      0,
        "taxable_pay":           0,
        "tax_on_income":         0,
        "personal_relief":       0,
        "insurance_relief":      0,
        "total_relief":          0,
        "tax_after_relief":      0,
        "paye_deducted":         0,
        "tax_balance":           0,

        # Status
        "status":         status,
        "status_message": status_message,
        "status_color":   status_color,
    }

    # Merge computed values in
    summary.update(computed)
    return summary