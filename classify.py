import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Your App Title", page_icon="📊", initial_sidebar_state="auto", menu_items={
    'Get Help': None,
    'Report a bug': None,
    'About': None
})

# ----------- Secure Authentication using st.secrets -----------
def verify_login(username, password):
    stored_password = st.secrets["auth"].get(username)
    return stored_password == password

# ----------- Session State for Login -----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Login Required")

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if verify_login(username, password):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()

# ----------- Logout Option -----------
def logout():
    st.session_state.authenticated = False

st.sidebar.button("🚪 Logout", on_click=logout)

if not st.session_state.authenticated:
    st.experimental_rerun()

# ----------- Categorization Logic -----------
def categorize(text):
    text = str(text).strip().lower()
    if "disburse" in text:
        return "Loan Disburse"
    elif any(x in text for x in ["rtgs", "rtg"]):
        return "RTGS Transfer"
    elif "cic" in text:
        return "CIC Charge"
    elif "valuation" in text:
        return "Valuation Charge"
    elif "insurance" in text:
        return "Insurance Charges"
    elif any(x in text for x in ["mgmt", "management", "service", "1%", "0.25%"]):
        return "Management and Service Charge"
    elif text.startswith("te") or text.startswith("t/e"):
        return "T/E Charge"
    elif any(x in text for x in ["fee", "charge", "iw clg chq rtn chg", "express chrg"]):
        return "Fee & Charges"
    elif "settle" in text:
        return "Loan Settlement"
    elif any(x in text for x in ["inc:ecc", "ow clg chq", "inward ecc chq", "owchq"]):
        return "Cheque - Other Bank"
    elif "home" in text:
        return "Cheque - Internal"
    elif "fpay" in text:
        return "PhonePay Transfer"
    elif "cash" in text or "dep by" in text:
        return "Cash Deposit"
    elif any(x in text for x in ["rebate", "discount"]):
        return "Discount & Rebate"
    elif "penal" in text:
        return "Penal Deduction"
    elif text.startswith("int to "):
        return "Interest Deduction"
    elif text.startswith("balnxfr"):
        return "Principal Repayment"
    elif any(x in text for x in ["trf", "from", "tran"]):
        return "Internal Transfer"
    elif any(x in text for x in ["accountft", "ips"]):
        return "IPS Transfer"
    elif "repay" in text:
        return "Repayment"
    elif "esewa" in text:
        return "Esewa Transfer"
    elif "mob" in text:
        return "Mobile Banking Transfer"
    elif "qr" in text:
        return "QR Deposit"
    else:
        return "Not Classified"

# ----------- App UI -----------
st.title("📊 Account Statement Categorizer")

st.markdown("""
### 📋 Instructions:
- File must be named: **ACCOUNT STATEMENT.xlsx**
- Must contain a sheet named **ACCOUNT STATEMENT**
- Must include a column named **Desc1**
""")

uploaded_file = st.file_uploader("📁 Upload your 'ACCOUNT STATEMENT.xlsx'", type=["xlsx"])

if uploaded_file:
    if uploaded_file.name.strip().lower() != "account statement.xlsx":
        st.warning("⚠️ Please upload the file exactly named 'ACCOUNT STATEMENT.xlsx'")
        st.stop()

    try:
        df = pd.read_excel(uploaded_file, sheet_name="ACCOUNT STATEMENT")
    except Exception as e:
        st.error(f"❌ Unable to read the Excel file: {e}")
        st.stop()

    # Drop irrelevant columns
    cols_to_remove = ["Branch Code", "Time Stamp", "Balance"]
    df = df.drop(columns=[col for col in cols_to_remove if col in df.columns])

    if "Desc1" not in df.columns:
        st.error("❌ 'Desc1' column not found in the uploaded Excel file.")
        st.stop()

    df = df[df['Desc1'] != "~Date summary"]

    # Ensure required columns exist
    for col in ["Desc1", "Desc2", "Desc3", "Tran Id"]:
        if col not in df.columns:
            df[col] = ""

    # Combine for categorization
    df["CombinedCol"] = (
        df["Desc1"].fillna('').astype(str).str.strip().str.lower() + ' ' +
        df["Desc2"].fillna('').astype(str).str.strip().str.lower() + ' ' +
        df["Desc3"].fillna('').astype(str).str.strip().str.lower() + ' ' +
        df["Tran Id"].fillna('').astype(str).str.strip().str.lower()
    )

    df["Category"] = df["CombinedCol"].apply(categorize)
    final_df = df.drop(columns=["CombinedCol"])

    # In-memory Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final_df.to_excel(writer, index=False, sheet_name='Categorized')
    output.seek(0)

    st.success("✅ File processed successfully!")
    st.download_button(
        label="📥 Download Categorized Excel File",
        data=output.getvalue(),
        file_name="categorized_account_statement.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
