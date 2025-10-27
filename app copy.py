import streamlit as st
import pandas as pd
from io import BytesIO

# --- Default Company URLs ---
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

# --- Streamlit UI ---
st.set_page_config(page_title="Company Financial Dashboard", layout="wide")
st.title("📊 Company Financial Dashboard")
st.markdown("Explore **Balance Sheet** and **Profit & Loss** data from Moneycontrol.")

# --- Input Section ---
col1, col2 = st.columns([2, 3])
with col1:
    company_choice = st.selectbox("Choose a company:", list(company_data.keys()) + ["Custom URL"])
with col2:
    st.info("💡 Select a company or enter your own Moneycontrol URLs below.")

custom_bs_url = st.text_input("🔗 Custom Balance Sheet URL (optional):")
custom_pl_url = st.text_input("🔗 Custom Profit & Loss URL (optional):")

# --- Get URLs based on user input ---
if company_choice != "Custom URL":
    urls = company_data[company_choice]
else:
    urls = {"BS_URL": custom_bs_url, "PL_URL": custom_pl_url}

# --- Cached fetch function ---
@st.cache_data(show_spinner=True)
def fetch_data(bs_url, pl_url):
    bs_df = pd.read_html(bs_url, header=0, skiprows=(1, 2, 3))[0].iloc[:, 0:6]
    pl_df = pd.read_html(pl_url, header=0, skiprows=(1, 2))[0].iloc[:, 0:6]
    return bs_df, pl_df

# --- Fetch Button ---
if st.button("🚀 Fetch Financial Data"):
    if not urls["BS_URL"] or not urls["PL_URL"]:
        st.error("⚠️ Please provide both Balance Sheet and Profit & Loss URLs.")
    else:
        try:
            bs_df, pl_df = fetch_data(urls["BS_URL"], urls["PL_URL"])

            st.success("✅ Data fetched successfully!")

            # --- Display Data ---
            st.subheader("📘 Balance Sheet")
            st.dataframe(bs_df, use_container_width=True)

            st.subheader("📗 Profit & Loss")
            st.dataframe(pl_df, use_container_width=True)

            # --- Visualization ---
            st.markdown("### 📈 Quick Visualization")
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Total Assets Trend (Balance Sheet)**")
                bs_df_melt = bs_df.melt(id_vars=bs_df.columns[0], var_name="Year", value_name="Value")
                bs_assets = bs_df_melt[bs_df_melt[bs_df.columns[0]].str.contains("Total Assets", case=False, na=False)]
                if not bs_assets.empty:
                    st.bar_chart(bs_assets.set_index("Year")["Value"])

            with col2:
                st.write("**Net Profit Trend (Profit & Loss)**")
                pl_df_melt = pl_df.melt(id_vars=pl_df.columns[0], var_name="Year", value_name="Value")
                pl_profit = pl_df_melt[pl_df_melt[pl_df.columns[0]].str.contains("Net Profit", case=False, na=False)]
                if not pl_profit.empty:
                    st.line_chart(pl_profit.set_index("Year")["Value"])

            # --- Excel Download ---
            combined_excel = BytesIO()
            with pd.ExcelWriter(combined_excel, engine='openpyxl') as writer:
                bs_df.to_excel(writer, sheet_name="Balance Sheet", index=False)
                pl_df.to_excel(writer, sheet_name="Profit & Loss", index=False)
            combined_excel.seek(0)

            st.download_button(
                label="⬇️ Download Full Report (Excel)",
                data=combined_excel,
                file_name=f"{company_choice.replace(' ', '_')}_Financials.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Failed to fetch or process data: {e}")
