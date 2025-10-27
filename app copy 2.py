import streamlit as st
import pandas as pd
from io import BytesIO
from fuzzywuzzy import process

# -------------------------------
#  Company Database (Preloaded)
# -------------------------------
company_data = {
    "JSW Steel": {
        "BS_URL": "https://www.moneycontrol.com/financials/jswsteel/balance-sheetVI/JSW01#JSW01",
        "PL_URL": "https://www.moneycontrol.com/financials/jswsteel/profit-lossVI/JSW01#JSW01"
    },
    "Grasim Industries": {
        "BS_URL": "https://www.moneycontrol.com/financials/grasimindustries/balance-sheetVI/GI#GI",
        "PL_URL": "https://www.moneycontrol.com/financials/grasimindustries/profit-lossVI/GI#GI"
    },
    "SBI Life Insurance": {
        "BS_URL": "https://www.moneycontrol.com/financials/sbilifeinsurancecompany/balance-sheetVI/SLI03#SLI03",
        "PL_URL": "https://www.moneycontrol.com/financials/sbilifeinsurancecompany/profit-lossVI/SLI03#SLI03"
    },
    "Axis Bank": {
        "BS_URL": "https://www.moneycontrol.com/financials/axisbank/balance-sheetVI/AB16#AB16",
        "PL_URL": "https://www.moneycontrol.com/financials/axisbank/consolidated-profit-lossVI/AB16#AB16"
    },
    "HDFC Bank": {
        "BS_URL": "https://www.moneycontrol.com/financials/hdfcbank/balance-sheetVI/HDF01#HDF01",
        "PL_URL": "https://www.moneycontrol.com/financials/hdfcbank/profit-lossVI/hdf01"
    }
}

# -------------------------------
# Streamlit Page Setup
# -------------------------------
st.set_page_config(page_title="Company Financials Explorer", layout="wide")
st.title("📊 Company Financials Explorer")
st.markdown("Type a company name to view its **Balance Sheet** and **Profit & Loss** from Moneycontrol.")

# -------------------------------
# User Input
# -------------------------------
user_input = st.text_input("🔎 Enter company name (e.g., HDFC, Axis, Grasim, JSW):").strip()

custom_bs_url = ""
custom_pl_url = ""

matched_company = None
if user_input:
    matched_company, score = process.extractOne(user_input, company_data.keys())
    if score >= 70:
        st.success(f"✅ Closest match found: **{matched_company}** ({score}%)")
    else:
        st.warning("⚠️ No close match found in database. Please enter URLs manually.")
        custom_bs_url = st.text_input("Enter Balance Sheet URL:")
        custom_pl_url = st.text_input("Enter Profit & Loss URL:")

# -------------------------------
# Cached fetch function
# -------------------------------
@st.cache_data(show_spinner=True)
def fetch_data(bs_url, pl_url):
    bs_df = pd.read_html(bs_url, header=0, skiprows=(1, 2, 3))[0].iloc[:, 0:6]
    pl_df = pd.read_html(pl_url, header=0, skiprows=(1, 2))[0].iloc[:, 0:6]
    return bs_df, pl_df

# -------------------------------
# Fetch & Display Button
# -------------------------------
if st.button("🚀 Fetch Financial Data"):
    try:
        if matched_company and matched_company in company_data:
            urls = company_data[matched_company]
        elif custom_bs_url and custom_pl_url:
            urls = {"BS_URL": custom_bs_url, "PL_URL": custom_pl_url}
        else:
            st.error("❌ Please provide valid input or URLs.")
            st.stop()

        bs_df, pl_df = fetch_data(urls["BS_URL"], urls["PL_URL"])
        st.success("📈 Data fetched successfully!")

        # -------------------------------
        # Display Tables
        # -------------------------------
        st.subheader("📘 Balance Sheet")
        st.dataframe(bs_df, use_container_width=True)

        st.subheader("📗 Profit & Loss")
        st.dataframe(pl_df, use_container_width=True)

        # -------------------------------
        # Charts Section
        # -------------------------------
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

        # -------------------------------
        # Excel Download
        # -------------------------------
        combined_excel = BytesIO()
        with pd.ExcelWriter(combined_excel, engine="openpyxl") as writer:
            bs_df.to_excel(writer, sheet_name="Balance Sheet", index=False)
            pl_df.to_excel(writer, sheet_name="Profit & Loss", index=False)
        combined_excel.seek(0)

        st.download_button(
            label="⬇️ Download Combined Report (Excel)",
            data=combined_excel,
            file_name=f"{(matched_company or 'Custom_Company').replace(' ', '_')}_Financials.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error fetching or processing data: {e}")
