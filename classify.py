import streamlit as st
import hashlib
import hmac

# 1️⃣ Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 2️⃣ Hardcoded hashed passwords
USERS = {
    "admin": "4c69744ac9a47ef87e18b170400f3490f165d68932580a630d994b94f203c898",     # securepass123
    "user1": "a5ec681f50fc07a4bca73882e832d2e101fbc3d7a3df0bc60c961fd5e1a81d0d",     # anotherpass456
}

# 3️⃣ Verify login
def verify_login(username, password):
    if username not in USERS:
        return False
    return hmac.compare_digest(USERS[username], hash_password(password))

# 4️⃣ Initialize session
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# 5️⃣ Login flow
if not st.session_state.authenticated:
    st.title("🔐 Secure Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if verify_login(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Login successful! Redirecting...")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid username or password")
    st.stop()

# 6️⃣ Logged-in content
st.sidebar.success(f"✅ Logged in as: {st.session_state.username}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.experimental_rerun()

st.title("🎉 Welcome!")
st.write("You're logged in. Your protected content goes here.")
