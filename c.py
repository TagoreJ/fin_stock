import pandas as pd
import re

# --- Input & Output ---
input_file = "EQUITY_L.csv"             # Your NSE master file
output_file = "moneycontrol_links.csv"  # Output file with URLs

# --- Read the NSE company data ---
df = pd.read_csv(input_file)

# --- Clean company names for URL format ---
def make_slug(name):
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)  # remove special chars
    name = re.sub(r"\s+", "", name)           # remove spaces
    return name

# --- Build URLs ---
records = []
for _, row in df.iterrows():
    company = str(row["NAME OF COMPANY"]).strip()
    symbol = str(row["SYMBOL"]).strip()

    slug = make_slug(company)
    bs_url = f"https://www.moneycontrol.com/financials/{slug}/balance-sheetVI/{symbol}#{symbol}"
    pl_url = f"https://www.moneycontrol.com/financials/{slug}/profit-lossVI/{symbol}#{symbol}"

    records.append({
        "Company": company,
        "Symbol": symbol,
        "BalanceSheetURL": bs_url,
        "ProfitLossURL": pl_url
    })

# --- Save output ---
out_df = pd.DataFrame(records)
out_df.to_csv(output_file, index=False)
print(f"✅ Saved {len(out_df)} company URLs to '{output_file}'")
