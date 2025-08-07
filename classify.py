import streamlit as st
import pandas as pd
from io import BytesIO
import hashlib
from concurrent.futures import ThreadPoolExecutor

# --- Authentication using Streamlit Secrets (GitHub usernames/passwords) ---

# Define a hashing function for password security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    # Streamlit secrets should contain a 'users' dict with username: hashed_password
    users = st.secrets.get("users", {})
    return username in users and users[username] == hash_password(password)

def login_block():
    st.title("🔐 Login")
    username = st.text_input("GitHub Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")
    if login_btn:
        if authenticate(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")
    st.stop()

# -- Only show login if not logged in
if not st.session_state.get("logged_in"):
    login_block()

# --- Category function (same as before) ---
def categorize(text):
    text = str(text).strip().lower()

    if "disburse" in text:
        return "Loan Disburse"
    elif any(x in text for x in ["rtgs", "rtg"]):
        return "RTGS Transfer"
    elif "cic" in text:
        return "CIC Charge"
    elif "valuation" in text:
        return "valuation Charge"
    elif "insurance" in text:
        return "Insurance Charges"
    elif any(x in text for x in ["mgmt", "management", "service", "1%", "0.25%"]):
        return "Management and service charge"
    elif text.startswith("te") or text.startswith("t/e"):
        return "T/E Charge"
    elif any(x in text for x in ["fee", "charge", "iw clg chq rtn chg", "express chrg"]):
        return "Fee & Charges"
    elif "settle" in text:
        return "Loan Settlement"
    elif any(x in text for x in ["inc:ecc", "ow clg chq", "inward ecc chq", "owchq"]):
        return "Cheque-Other Bank"
    elif "home" in text:
        return "Cheque-Internal"
    elif "fpay" in text:
        return "Phonepay transfer"
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
        return "Mobile Banking transfer"
    elif "qr" in text:
        return "QR Deposit"
    else:
        return "Not Classified"

# --- Sidebar Dashboard ---
st.sidebar.title("📊 Dashboard")
st.sidebar.write(f"👤 Logged in as: {st.session_state['username']}")

# Optionally, add a logout button
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# --- Main App: Multiple Upload & Parallel Processing ---

st.title("📑 Multi-Account Statement Categorizer")

uploaded_files = st.file_uploader(
    "📁 Upload one or more 'ACCOUNT STATEMENT.xlsx' files", 
    type=["xlsx"], 
    accept_multiple_files=True
)

def process_file(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, sheet_name="ACCOUNT STATEMENT")
    except Exception as e:
        return None, f"❌ Failed to read {uploaded_file.name}: {e}"

    # Remove unnecessary columns if they exist
    cols_to_remove = ["Branch Code", "Time Stamp", "Balance"]
    df = df.drop(columns=[col for col in cols_to_remove if col in df.columns])

    if 'Desc1' not in df.columns:
        return None, f"❌ 'Desc1' column not found in {uploaded_file.name}."

    df = df[df['Desc1'] != "~Date summary"]

    # Ensure required columns exist
    for col in ["Desc1", "Desc2", "Desc3", "Tran Id"]:
        if col not in df.columns:
            df[col] = ""

    # Clean and combine text for classification
    df["CombinedCol"] = (
        df["Desc1"].fillna('').astype(str).str.strip().str.lower() + ' ' +
        df["Desc2"].fillna('').astype(str).str.strip().str.lower() + ' ' +
        df["Desc3"].fillna('').astype(str).str.strip().str.lower() + ' ' +
        df["Tran Id"].fillna('').astype(str).str.strip().str.lower()
    )

    # Apply categorization
    df["Category"] = df["CombinedCol"].apply(categorize)

    # Drop the combined column before output
    final_df = df.drop(columns=["CombinedCol"])

    # Convert to Excel in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final_df.to_excel(writer, index=False, sheet_name='Categorized')
    output.seek(0)

    return {
        "df": final_df,
        "excel": output.getvalue(),
        "name": uploaded_file.name
    }, None

def process_files_parallel(uploaded_files):
    results = []
    errors = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_file, file) for file in uploaded_files]
        for fut in futures:
            result, error = fut.result()
            if error:
                errors.append(error)
            else:
                results.append(result)
    return results, errors

if uploaded_files:
    with st.spinner("🔄 Processing files..."):
        results, errors = process_files_parallel(uploaded_files)
    if errors:
        for error in errors:
            st.error(error)
    for result in results:
        st.success(f"✅ {result['name']} processed successfully!")
        with st.expander(f"Preview: {result['name']}", expanded=False):
            st.dataframe(result["df"].head(), use_container_width=True)
        st.download_button(
            label=f"📥 Download {result['name'].replace('.xlsx', '')}_categorized.xlsx",
            data=result["excel"],
            file_name=f"{result['name'].replace('.xlsx', '')}_categorized.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- Dashboard for Category Distribution Across All Uploaded Files ---
if uploaded_files:
    st.header("📈 Category Dashboard")
    all_dfs = [r['df'] for r in results if r]
    if all_dfs:
        merged = pd.concat(all_dfs, ignore_index=True)
        cat_counts = merged['Category'].value_counts().rename_axis('Category').reset_index(name='Count')
        st.bar_chart(cat_counts.set_index("Category"))
        with st.expander("Show category counts table"):
            st.dataframe(cat_counts)
