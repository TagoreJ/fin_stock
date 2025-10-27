import pandas as pd
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Input & Output ---
input_file = "EQUITY_L.csv"             # NSE company master list
output_file = "verified_moneycontrol_links.csv"  # Final output

# --- Read input data ---
df = pd.read_csv(input_file)

# --- Function to clean company names for URLs ---
def make_slug(name):
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"\s+", "", name)
    return name.strip()

# --- Generate URL pair for each company ---
def generate_urls(company, symbol):
    slug = make_slug(company)
    bs_url = f"https://www.moneycontrol.com/financials/{slug}/balance-sheetVI/{symbol}#{symbol}"
    pl_url = f"https://www.moneycontrol.com/financials/{slug}/profit-lossVI/{symbol}#{symbol}"
    return bs_url, pl_url

# --- Verify URL existence ---
def verify_url(url):
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False

# --- Parallel verification ---
results = []
with ThreadPoolExecutor(max_workers=15) as executor:
    futures = {}
    for _, row in df.iterrows():
        company = str(row["NAME OF COMPANY"]).strip()
        symbol = str(row["SYMBOL"]).strip()
        bs_url, pl_url = generate_urls(company, symbol)
        futures[executor.submit(verify_url, bs_url)] = (company, symbol, bs_url, pl_url)
    
    for future in as_completed(futures):
        company, symbol, bs_url, pl_url = futures[future]
        valid_bs = future.result()
        valid_pl = verify_url(pl_url)
        if valid_bs or valid_pl:
            results.append({
                "Company": company,
                "Symbol": symbol,
                "BalanceSheetURL": bs_url,
                "ProfitLossURL": pl_url,
                "BS_Valid": valid_bs,
                "PL_Valid": valid_pl
            })

# --- Save only valid entries ---
verified_df = pd.DataFrame(results)
verified_df.to_csv(output_file, index=False)
print(f"✅ Verified URLs saved: {len(verified_df)} companies")
print(f"📁 Output file: {output_file}")
