import streamlit as st
import hashlib
import hmac

# ----------- Password Hashing -----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ----------- User Hashes (precomputed) -----------
USERS = {
    "admin": "4c69744ac9a47ef87e18b170400f3490f165d68932580a630d994b94f203c898",       # securepass123
    "user1": "a5ec681f50fc07a4bca73882e832d2e101fbc3d7a3df0bc60c961fd5e1a81d0d",     # anotherpass456
}

# ----------- Auth Check -----------
def verify_login(username, password):
    stored_hash = USERS.get(username)
    if not stored_hash:
        return False
    return hmac.compare_digest(stored_hash, hash_password(password))

# ----------- Session State -----------
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
            st.success("✅ Login successful! Please wait...")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
    st.stop()

# ----------- Logged In -----------
st.sidebar.button("🚪 Logout", on_click=lambda: st.session_state.update({"authenticated": False}) or st.rerun())

st.title("🎉 You are logged in!")
st.write("Now you can access the rest of the app.")
