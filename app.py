import streamlit as st
import pandas as pd
from fuzzywuzzy import process
from io import BytesIO
import requests
from lxml import html

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(page_title="Company Financials Explorer", layout="wide")
st.title("📊 Company Financials Explorer")
st.markdown("View **Balance Sheet** and **Profit & Loss** data from [Moneycontrol](https://www.moneycontrol.com).")

# -----------------------------------
# LOAD COMPANY DATABASE
# -----------------------------------
@st.cache_data
def load_company_data():
    df = pd.read_csv("moneycontrol_links.csv")
    df.dropna(subset=["BalanceSheetURL", "ProfitLossURL"], inplace=True)
    company_dict = {
        row["Company"]: {
            "BS_URL": row["BalanceSheetURL"],
            "PL_URL": row["ProfitLossURL"]
        }
        for _, row in df.iterrows()
    }
    return company_dict

company_data = load_company_data()
company_names = list(company_data.keys())

# -----------------------------------
# AUTOCOMPLETE DROPDOWN USING FUZZY MATCH
# -----------------------------------
st.sidebar.header("🔎 Company Search")

def suggest_matches(user_input, choices, limit=5):
    if not user_input:
        return []
    matches = process.extract(user_input, choices, limit=limit)
    return [m[0] for m in matches if m[1] >= 60]

user_input = st.sidebar.text_input("Type company name:").strip()
suggestions = suggest_matches(user_input, company_names)

selected_company = None
if suggestions:
    selected_company = st.sidebar.selectbox("📍 Suggestions:", suggestions)
else:
    st.sidebar.info("Type at least 3 letters to see suggestions.")

custom_bs_url = ""
custom_pl_url = ""

if not selected_company and user_input:
    st.sidebar.warning("⚠️ No close match found. Enter URLs manually.")
    custom_bs_url = st.sidebar.text_input("Enter Balance Sheet URL:")
    custom_pl_url = st.sidebar.text_input("Enter Profit & Loss URL:")

# -----------------------------------
# FETCH & PARSE DATA SAFELY
# -----------------------------------
@st.cache_data(show_spinner=True)
def fetch_tables(url):
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        tree = html.fromstring(response.content)
        tables = pd.read_html(response.text)
        return tables[0] if tables else None
    except Exception:
        return None

# -----------------------------------
# FETCH BUTTON
# -----------------------------------
if st.sidebar.button("🚀 Fetch Financial Data"):
    try:
        if selected_company:
            urls = company_data[selected_company]
        elif custom_bs_url and custom_pl_url:
            urls = {"BS_URL": custom_bs_url, "PL_URL": custom_pl_url}
        else:
            st.error("❌ Please select a valid company or enter URLs manually.")
            st.stop()

        bs_df = fetch_tables(urls["BS_URL"])
        pl_df = fetch_tables(urls["PL_URL"])

        if bs_df is None or pl_df is None:
            st.error("❌ No financial tables found. The Moneycontrol page might have changed or the company data is unavailable.")
            st.stop()

        # Display Results
        st.success(f"📈 Data fetched successfully for **{selected_company or 'Custom Company'}**")

        st.subheader("📘 Balance Sheet")
        st.dataframe(bs_df, use_container_width=True)

        st.subheader("📗 Profit & Loss Statement")
        st.dataframe(pl_df, use_container_width=True)

        # -----------------------------------
        # VISUALIZATION
        # -----------------------------------
        st.markdown("### 📊 Financial Highlights")
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Total Assets Trend (Balance Sheet)**")
            bs_melt = bs_df.melt(id_vars=bs_df.columns[0], var_name="Year", value_name="Value")
            assets = bs_melt[bs_melt[bs_df.columns[0]].str.contains("Total Assets", case=False, na=False)]
            if not assets.empty:
                st.bar_chart(assets.set_index("Year")["Value"])

        with col2:
            st.write("**Net Profit Trend (Profit & Loss)**")
            pl_melt = pl_df.melt(id_vars=pl_df.columns[0], var_name="Year", value_name="Value")
            profits = pl_melt[pl_melt[pl_df.columns[0]].str.contains("Net Profit", case=False, na=False)]
            if not profits.empty:
                st.line_chart(profits.set_index("Year")["Value"])

        # -----------------------------------
        # DOWNLOAD REPORT
        # -----------------------------------
        combined_excel = BytesIO()
        with pd.ExcelWriter(combined_excel, engine="openpyxl") as writer:
            bs_df.to_excel(writer, sheet_name="Balance Sheet", index=False)
            pl_df.to_excel(writer, sheet_name="Profit & Loss", index=False)
        combined_excel.seek(0)

        st.download_button(
            label="⬇️ Download Full Report (Excel)",
            data=combined_excel,
            file_name=f"{(selected_company or 'Custom_Company').replace(' ', '_')}_Financials.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error fetching or processing data: {e}")
