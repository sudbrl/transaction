import streamlit as st
import pandas as pd
from io import BytesIO
import hashlib
from concurrent.futures import ThreadPoolExecutor

# --- Password Hashing ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Authentication Function ---
def authenticate(username, password):
    users = st.secrets.get("users", None)
    if users is None:
        st.error("⚠️ No users found in secrets. Please configure `.streamlit/secrets.toml`.")
        st.stop()
    return username in users and users[username] == hash_password(password)

# --- Login Interface ---
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

# --- Run login if not authenticated ---
if not st.session_state.get("logged_in"):
    login_block()

# --- Sidebar ---
st.sidebar.title("📊 Dashboard")
st.sidebar.write(f"👤 Logged in as: {st.session_state['username']}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# --- Categorization Logic ---
def categorize(text):
    text = str(text).strip().lower()

    rules = [
        (["disburse"], "Loan Disburse"),
        (["rtgs", "rtg"], "RTGS Transfer"),
        (["cic"], "CIC Charge"),
        (["valuation"], "valuation Charge"),
        (["insurance"], "Insurance Charges"),
        (["mgmt", "management", "service", "1%", "0.25%"], "Management and service charge"),
        (["te", "t/e"], "T/E Charge"),
        (["fee", "charge", "iw clg chq rtn chg", "express chrg"], "Fee & Charges"),
        (["settle"], "Loan Settlement"),
        (["inc:ecc", "ow clg chq", "inward ecc chq", "owchq"], "Cheque-Other Bank"),
        (["home"], "Cheque-Internal"),
        (["fpay"], "Phonepay transfer"),
        (["cash", "dep by"], "Cash Deposit"),
        (["rebate", "discount"], "Discount & Rebate"),
        (["penal"], "Penal Deduction"),
        (["int to "], "Interest Deduction"),
        (["balnxfr"], "Principal Repayment"),
        (["trf", "from", "tran"], "Internal Transfer"),
        (["accountft", "ips"], "IPS Transfer"),
        (["repay"], "Repayment"),
        (["esewa"], "Esewa Transfer"),
        (["mob"], "Mobile Banking transfer"),
        (["qr"], "QR Deposit"),
    ]

    for keywords, category in rules:
        if any(k in text for k in keywords):
            return category
    return "Not Classified"

# --- File Processor ---
def process_file(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, sheet_name="ACCOUNT STATEMENT")
    except Exception as e:
        return None, f"❌ Failed to read {uploaded_file.name}: {e}"

    # Drop irrelevant columns if they exist
    cols_to_remove = ["Branch Code", "Time Stamp", "Balance"]
    df.drop(columns=[col for col in cols_to_remove if col in df.columns], inplace=True)

    if 'Desc1' not in df.columns:
        return None, f"❌ 'Desc1' column not found in {uploaded_file.name}."

    # Remove header rows or summaries
    df = df[df['Desc1'] != "~Date summary"]

    # Ensure necessary columns
    for col in ["Desc1", "Desc2", "Desc3", "Tran Id"]:
        if col not in df.columns:
            df[col] = ""

    # Combine for classification
    df["CombinedCol"] = (
        df["Desc1"].fillna('').astype(str).str.strip().str.lower() + ' ' +
        df["Desc2"].fillna('').astype(str).str.strip().str.lower() + ' ' +
        df["Desc3"].fillna('').astype(str).str.strip().str.lower() + ' ' +
        df["Tran Id"].fillna('').astype(str).str.strip().str.lower()
    )

    df["Category"] = df["CombinedCol"].apply(categorize)
    df.drop(columns=["CombinedCol"], inplace=True)

    # Convert to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Categorized')
    output.seek(0)

    return {
        "df": df,
        "excel": output.getvalue(),
        "name": uploaded_file.name
    }, None

# --- Parallel File Processor ---
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

# --- File Uploader ---
st.title("📑 Multi-Account Statement Categorizer")

uploaded_files = st.file_uploader(
    "📁 Upload one or more 'ACCOUNT STATEMENT.xlsx' files",
    type=["xlsx"],
    accept_multiple_files=True
)

# --- File Processing ---
if uploaded_files:
    with st.spinner("🔄 Processing files..."):
        results, errors = process_files_parallel(uploaded_files)

    # Display errors
    if errors:
        for error in errors:
            st.error(error)

    # Display results
    for idx, result in enumerate(results):
        st.success(f"✅ {result['name']} processed successfully!")
        with st.expander(f"🔍 Preview: {result['name']}", expanded=(idx == 0)):
            st.dataframe(result["df"].head(), use_container_width=True)

        short_name = result["name"].replace('.xlsx', '')[:30]
        st.download_button(
            label=f"📥 Download {short_name}_categorized.xlsx",
            data=result["excel"],
            file_name=f"{short_name}_categorized.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- Dashboard ---
    st.header("📈 Category Dashboard")
    all_dfs = [r['df'] for r in results if r]
    if all_dfs:
        merged = pd.concat(all_dfs, ignore_index=True)
        cat_counts = merged['Category'].value_counts().rename_axis('Category').reset_index(name='Count')
        st.bar_chart(cat_counts.set_index("Category"))
        with st.expander("📋 Show category counts table"):
            st.dataframe(cat_counts)
