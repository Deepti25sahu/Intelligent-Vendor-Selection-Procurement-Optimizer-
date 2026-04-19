import streamlit as st
from database import register_user, login_user, create_user_table

def auth_screen():
    create_user_table()

    st.sidebar.title("🔐 Authentication")
    choice = st.sidebar.radio("Select", ["Login", "Register"])

    # ---------------- REGISTER ----------------
    if choice == "Register":
        st.subheader("📝 Create Account")

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["user", "admin"])

        if st.button("Register"):
            if not u or not p:
                st.error("⚠️ Please fill all fields")
            else:
                success = register_user(u, p, role)

                if success:
                    st.success("✅ Account created! Please login.")
                else:
                    st.error("❌ Username already exists")

    # ---------------- LOGIN ----------------
    else:
        st.subheader("🔐 Login")

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            if not u or not p:
                st.error("⚠️ Enter username and password")
            else:
                user = login_user(u, p)

                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = user[0]
                    st.session_state["role"] = user[2]

                    st.success(f"Welcome, {user[0]} 👋")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

# ---------------- CHECK LOGIN ----------------
def check_login():
    return st.session_state.get("logged_in", False)