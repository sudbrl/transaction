import streamlit as st
import hashlib
import hmac

# Hash password using SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Precomputed hashes
USERS = {
    "admin": "4c69744ac9a47ef87e18b170400f3490f165d68932580a630d994b94f203c898",  # securepass123
    "user1": "a5ec681f50fc07a4bca73882e832d2e101fbc3d7a3df0bc60c961fd5e1a81d0d",  # anotherpass456
}

# Login verification
def verify_login(username, password):
    stored_hash = USERS.get(username)
    if not stored_hash:
        return False
    return hmac.compare_digest(stored_hash, hash_password(password))

# Initialize session
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Login form
if not st.session_state.authenticated:
    st.title("🔐 Login Required")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if verify_login(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Login successful!")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid username or password")

    st.stop()

# App content after login
st.sidebar.success(f"Logged in as: {st.session_state.username}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.experimental_rerun()

st.title("🎉 Welcome to the app!")
st.write("You're now logged in.")
