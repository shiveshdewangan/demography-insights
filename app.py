import streamlit as st
import pandas as pd
import json
import os
import hashlib
import re

from agent.prompts import ask_question


# -------------------------------
# FILE PATHS
# -------------------------------
USERS_FILE = "users.json"
CHAT_DIR = "chat_history"

os.makedirs(CHAT_DIR, exist_ok=True)


# -------------------------------
# UTIL FUNCTIONS
# -------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


def load_chat(username):
    path = f"{CHAT_DIR}/{username}.json"
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def save_chat(username, chat):
    with open(f"{CHAT_DIR}/{username}.json", "w") as f:
        json.dump(chat, f)


# -------------------------------
# PARSER (same as before)
# -------------------------------
def parse_response(text):
    data = []

    pattern = r"(.+): Rental Access ([\d.]+)%, Social Housing ([\d.]+)%"
    matches = re.findall(pattern, text)

    if matches:
        for m in matches:
            data.append(
                {
                    "Suburb": m[0].strip(),
                    "Rental Access (%)": float(m[1]),
                    "Social Housing (%)": float(m[2]),
                }
            )
        return pd.DataFrame(data)

    if ":" in text:
        possible_list = text.split(":")[-1]
        possible_list = possible_list.replace(" and ", ",")
        suburbs = [s.strip() for s in possible_list.split(",") if s.strip()]

        if len(suburbs) > 1:
            return pd.DataFrame({"Suburb": suburbs})

    return None


# -------------------------------
# AUTH UI
# -------------------------------
def login_signup():
    st.sidebar.title("🔐 Login / Signup")

    choice = st.sidebar.radio("Choose", ["Login", "Signup"])

    users = load_users()

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if choice == "Signup":
        if st.sidebar.button("Create Account"):
            if username in users:
                st.sidebar.error("User already exists")
            else:
                users[username] = {
                    "password": hash_password(password),
                    "usage": 0,
                    "paid": False,
                }
                save_users(users)
                st.sidebar.success("Account created!")

    else:
        if st.sidebar.button("Login"):
            if username in users and users[username]["password"] == hash_password(
                password
            ):
                st.session_state.user = username
                st.success(f"Welcome {username} 👋")
            else:
                st.error("Invalid credentials")


# -------------------------------
# MAIN APP
# -------------------------------
st.set_page_config(page_title="Suburb AI SaaS", layout="wide")

login_signup()


if "user" not in st.session_state:
    st.warning("Please login to continue")
    st.stop()


user = st.session_state.user
users = load_users()

st.title("🏡 Suburb Finder AI")

# -------------------------------
# LOAD CHAT HISTORY
# -------------------------------
chat_history = load_chat(user)

for chat in chat_history:
    with st.chat_message(chat["role"]):
        st.write(chat["content"])


# -------------------------------
# INPUT
# -------------------------------
prompt = st.chat_input("Ask your question...")


if prompt:

    # -------------------------------
    # FREE TIER CHECK
    # -------------------------------
    usage = users[user]["usage"]
    is_paid = users[user]["paid"]

    if usage >= 3 and not is_paid:
        st.error("🚫 Free limit reached. Please upgrade to continue.")

        if st.button("💳 Upgrade (Mock Payment)"):
            users[user]["paid"] = True
            save_users(users)
            st.success("Payment successful! Unlimited access enabled.")
        st.stop()

    # -------------------------------
    # SAVE USER MESSAGE
    # -------------------------------
    chat_history.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    # -------------------------------
    # AI RESPONSE
    # -------------------------------
    response = ask_question(prompt)

    with st.chat_message("assistant"):
        st.write(response)

        df = None

        if isinstance(response, pd.DataFrame):
            df = response
        elif isinstance(response, list):
            df = pd.DataFrame(response)
        elif isinstance(response, str):
            df = parse_response(response)

        if df is not None and not df.empty:
            st.dataframe(df)

            numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns

            if len(numeric_cols) > 0:
                st.bar_chart(df.set_index(df.columns[0])[numeric_cols[0]])

    # -------------------------------
    # SAVE CHAT
    # -------------------------------
    chat_history.append({"role": "assistant", "content": str(response)})
    save_chat(user, chat_history)

    # -------------------------------
    # UPDATE USAGE
    # -------------------------------
    users[user]["usage"] += 1
    save_users(users)
