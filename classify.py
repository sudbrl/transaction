import streamlit as st
import pandas as pd
from io import BytesIO
import tempfile
import os

st.set_page_config(
    page_title="Transaction Categorizer", 
    page_icon="📊", 
    initial_sidebar_state="auto", 
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# --- Hide Streamlit UI components ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ----------- Secure Authentication -----------
def verify_login(username, password):
    """Securely verify login credentials"""
    if not username or not password:
        return False
    stored_password = st.secrets["auth"].get(username)
    return stored_password and stored_password == password

# ----------- Session Management -----------
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
            st.session_state.username = username
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()

# ----------- Logout -----------
def logout():
    """Secure logout with session cleanup"""
    st.session_state.clear()
    st.session_state.authenticated = False

st.sidebar.button("🚪 Logout", on_click=logout)

# ----------- Categorization Logic -----------
def categorize(text):
    """Categorize transaction text with enhanced matching"""
    text = str(text).strip().lower()
    patterns = {
        "Loan Disburse": ["disburse"],
        "RTGS Transfer": ["rtgs", "rtg"],
        "CIC Charge": ["cic"],
        "Valuation Charge": ["valuation"],
        "Insurance Charges": ["insurance"],
        "Management and Service Charge": ["mgmt", "management", "service", "1%", "0.25%"],
        "T/E Charge": ["te", "t/e"],
        "Fee & Charges": ["fee", "charge", "iw clg chq rtn chg", "express chrg"],
        "Loan Settlement": ["settle"],
        "Cheque - Other Bank": ["inc:ecc", "ow clg chq", "inward ecc chq", "owchq"],
        "Cheque - Internal": ["home"],
        "PhonePay Transfer": ["fpay"],
        "Cash Deposit": ["cash", "dep by"],
        "Discount & Rebate": ["rebate", "discount"],
        "Penal Deduction": ["penal"],
        "Interest Deduction": ["int to"],
        "Principal Repayment": ["balnxfr"],
        "Internal Transfer": ["trf", "from", "tran"],
        "IPS Transfer": ["accountft", "ips"],
        "Repayment": ["repay"],
        "Esewa Transfer": ["esewa"],
        "Mobile Banking Transfer": ["mob"],
        "QR Deposit": ["qr"]
    }
    
    for category, keywords in patterns.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Not Classified"

# ----------- Secure File Processing -----------
def process_file(uploaded_file):
    """Process uploaded file with security checks"""
    try:
        # Use temporary file for processing
        with tempfile.NamedTemporaryFile(delete=True, suffix='.xlsx') as tmp_file:
            # Write to temp file
            tmp_file.write(uploaded_file.getvalue())
            tmp_file.flush()
            
            # Try reading with default sheet name first
            try:
                df = pd.read_excel(
                    tmp_file.name, 
                    sheet_name="ACCOUNT STATEMENT",
                    engine='openpyxl'
                )
            except:
                # If default sheet name fails, try first sheet
                df = pd.read_excel(
                    tmp_file.name, 
                    sheet_name=0,  # First sheet
                    engine='openpyxl'
                )
            
            # Validate required columns
            if "Desc1" not in df.columns:
                raise ValueError("Required column 'Desc1' not found in the uploaded file")
            
            # Clean data
            cols_to_remove = ["Branch Code", "Time Stamp", "Balance"]
            df = df.drop(columns=[col for col in cols_to_remove if col in df.columns])
            
            # Remove date summary rows if they exist
            if 'Desc1' in df.columns:
                df = df[df['Desc1'] != "~Date summary"]
            
            # Ensure optional columns exist
            for col in ["Desc2", "Desc3", "Tran Id"]:
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
            return df.drop(columns=["CombinedCol"])
            
    except Exception as e:
        st.error(f"❌ File processing error: {str(e)}")
        raise

# ----------- Main App UI -----------
st.title("📊 Transaction Categorizer")

st.markdown("""
### 📋 Instructions:
- Upload an Excel file containing transaction data
- File should contain a column named **Desc1** for categorization
- Other optional columns: Desc2, Desc3, Tran Id
""")

uploaded_file = st.file_uploader(
    "📁 Upload your Excel file", 
    type=["xlsx"],
    accept_multiple_files=False
)

if uploaded_file:
    try:
        # Secure processing
        final_df = process_file(uploaded_file)
        
        # Create in-memory output
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            final_df.to_excel(writer, index=False, sheet_name='Categorized')
        output.seek(0)
        
        # Show preview
        st.subheader("Preview of Categorized Data")
        st.dataframe(final_df.head())
        
        # Download button
        original_filename = os.path.splitext(uploaded_file.name)[0]
        download_filename = f"{original_filename}_categorized.xlsx"
        
        st.download_button(
            label="📥 Download Categorized File",
            data=output.getvalue(),
            file_name=download_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Clean up
        del final_df
        output.close()
        
    except Exception as e:
        st.error(f"❌ Processing failed: {e}")
