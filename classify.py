import streamlit as st
import pandas as pd
from io import BytesIO

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

# Streamlit app
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
