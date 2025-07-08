import streamlit as st
import hashlib
import hmac

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Expected hashes
USERS = {
    "admin": "4c69744ac9a47ef87e18b170400f3490f165d68932580a630d994b94f203c898",  # securepass123
    "user1": "a5ec681f50fc07a4bca73882e832d2e101fbc3d7a3df0bc60c961fd5e1a81d0d",  # anotherpass456
}

def verify_login(username, password):
    hashed_input = hash_password(password)
    stored_hash = USERS.get(username)
    return stored_hash and hmac.compare_digest(hashed_input, stored_hash)

# Start session
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""

if not st.session_state.authenticated:
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            if verify_login(username.strip(), password.strip()):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Login successful!")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid username or password")

    st.stop()

st.sidebar.success(f"✅ Logged in as: {st.session_state.username}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.experimental_rerun()

st.title("🎉 You're In!")
