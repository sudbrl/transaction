import streamlit as st
import pandas as pd
from io import BytesIO
import streamlit_authenticator as stauth

# ------------------------
# User authentication setup
# ------------------------

# Replace these hashed passwords with your own generated hashes
# To generate hashes run:
# import streamlit_authenticator as stauth
# print(stauth.Hasher(['your_password']).generate())
hashed_passwords = [
    'sha256$e3fa2d01db30f52b60e6c8b96038a8c836b49ee6bfe4bfb7cfaf3a8c5e9ac7e0'
]

credentials = {
    "usernames": {
        "alice": {"name": "Alice", "password": hashed_passwords[0]}
        # Add more users here if needed
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name="account_statement_cookie",
    key="random_signature_key",  # Change this to a strong random key
    cookie_expiry_days=1
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.write(f"Welcome *{name}*")

    # ------------------------
    # Your existing app code
    # ------------------------

    # Function to categorize text
    def categorize(text):
        text = str(text).strip().lower()

        if "disburse" in text:
            return "Loan Disburse"
        elif any(x in text for x in ["rtgs", "rtg"]):
            return "RTGS Transfer"
        elif any(x in text for x in ["fee", "charge"]):
            return "Fee & Charges"
        elif "settle" in text:
            return "Loan Settlement"
        elif "inc:ecc" in text:
            return "Cheque-Other Bank"
        elif "home" in text:
            return "Cheque-Internal"
        elif "fpay" in text:
            return "Phonepay transfer"
        elif "cash" in text:
            return "Cash Deposit"
        elif any(x in text for x in ["rebate", "discount"]):
            return "Discount & Rebate"
        elif "penal" in text:
            return "Penal Deduction"
        elif text.startswith("int to "):
            return "Interest Deduction"
        elif text.startswith("balnxfr"):
            return "Principal Repayment"
        elif "cic" in text:
            return "CIC Charge"
        elif "insurance" in text or "ins" in text:
            return "Insurance Charges"
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
        else:
            return "Not Classified"

    st.title("Account Statement Categorizer")

    uploaded_file = st.file_uploader("Upload 'ACCOUNT STATEMENT.xlsx'", type=["xlsx"])

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, sheet_name="ACCOUNT STATEMENT")
        except Exception as e:
            st.error(f"Failed to read Excel file: {e}")
            st.stop()

        # Remove unnecessary columns if they exist
        cols_to_remove = ["Branch Code", "Time Stamp", "Balance"]
        df = df.drop(columns=[col for col in cols_to_remove if col in df.columns])

        # Remove summary rows
        df = df[df['Desc1'] != "~Date summary"]

        # Combine relevant columns
        df["CombinedCol"] = (
            df["Desc1"].fillna('') + ' ' +
            df["Desc2"].fillna('') + ' ' +
            df["Desc3"].fillna('') + ' ' +
            df["Tran Id"].fillna('')
        ).str.lower().str.strip()

        # Apply categorization
        df["Category"] = df["CombinedCol"].apply(categorize)

        # Drop the combined column before output
        final_df = df.drop(columns=["CombinedCol"])

        # Convert to Excel in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            final_df.to_excel(writer, index=False, sheet_name='Categorized')

        st.success("✅ File processed and ready to download")

        st.download_button(
            label="📥 Download Categorized Excel File",
            data=output.getvalue(),
            file_name="categorized_account_statement.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    authenticator.logout("Logout", "sidebar")

elif authentication_status is False:
    st.error("Username/password is incorrect")

elif authentication_status is None:
    st.warning("Please enter your username and password")
