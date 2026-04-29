import streamlit as st
import pandas as pd
import json
import os
import re

from agent.prompts import ask_question
from auth.login import login_signup
from auth.users import get_usage, increment_usage
from auth.rbac import is_within_limit, get_usage_limit, is_near_limit

# -------------------------------
# FILE PATHS
# -------------------------------
CHAT_DIR = "chat_history"
os.makedirs(CHAT_DIR, exist_ok=True)


# -------------------------------
# CHAT HISTORY
# -------------------------------
def load_chat(user_id):
    path = f"{CHAT_DIR}/{user_id}.json"
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def save_chat(user_id, chat):
    with open(f"{CHAT_DIR}/{user_id}.json", "w") as f:
        json.dump(chat, f)


# -------------------------------
# PARSER
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
# MAIN APP
# -------------------------------
st.set_page_config(page_title="Suburb AI SaaS", layout="wide")

# Styling
st.markdown(
    """
<style>

/* Import Open Sauce Font */
@import url('https://fonts.cdnfonts.com/css/open-sauce-one');

/* Apply font globally */
html, body, [class*="css"]  {
    font-family: 'Open Sauce One', sans-serif;
}

/* Background */
.stApp {
    background: linear-gradient(180deg, #ffffff, #f5f7fb);
}

/* Title Styling */
h1 {
    background: linear-gradient(90deg, #8df2ed, #5e17eb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Chat bubbles */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 12px;
}

/* User message */
[data-testid="stChatMessage"][data-testid*="user"] {
    background: #f0f2f6;
}

/* Assistant message */
[data-testid="stChatMessage"][data-testid*="assistant"] {
    background: linear-gradient(135deg, #8df2ed, #e8eaff);
}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #8df2ed, #5e17eb);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 600;
}

.stButton>button:hover {
    opacity: 0.9;
}

/* Warning / Alerts */
.custom-warning {
    background: #e67e22;
    color: white;
    border-radius: 8px;
    padding: 12px;
}

.custom-error {
    background: #c0392b;
    color: white;
    border-radius: 8px;
    padding: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)
# End of styling

st.image("assets/logo.png", width=300)

with st.sidebar:
    st.image("assets/logo1.png", width=80)

st.markdown(
    """
<div style="
    background: linear-gradient(135deg, #8df2ed, #5e17eb);
    padding: 16px;
    border-radius: 10px;
    color: white;
    font-weight: 600;
">
    🏡 Find the best suburbs with AI insights
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>

/* Fix ALL chat message text visibility */
[data-testid="stChatMessage"] {
    color: #272d2d !important;
}

/* Ensure nested elements (markdown, code, etc.) are visible */
[data-testid="stChatMessage"] * {
    color: #272d2d !important;
}

/* Assistant message background */
[data-testid="stChatMessage"][data-testid*="assistant"] {
    background: #f5f7fb;
    border-radius: 12px;
    padding: 12px;
}

/* User message */
[data-testid="stChatMessage"][data-testid*="user"] {
    background: #eaeef6;
    border-radius: 12px;
    padding: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)

login_signup()

if "user" not in st.session_state:
    st.warning("Please login to continue")
    st.stop()

user = st.session_state.user
tier = st.session_state.get("tier", "free")

# st.title("🏡 Suburb Finder AI")

# -------------------------------
# TIER LIMIT CHECK
# -------------------------------
usage = get_usage(user)

if not is_within_limit(usage, tier):
    limit = get_usage_limit(tier)
    st.markdown(
        f"""
        <div style="background:#c0392b;color:#fff;padding:16px 20px;
                    border-radius:8px;font-size:16px;font-weight:600;margin-bottom:12px;">
            🚫 You have exhausted your <strong>{tier}</strong> tier limit of
            <strong>{limit}</strong> questions.
            Your limit resets 24 hours after your last login.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

if is_near_limit(usage, tier):
    limit = get_usage_limit(tier)
    pct = int(usage / limit * 100)
    st.markdown(
        f"""
        <div style="background:#e67e22;color:#fff;padding:16px 20px;
                    border-radius:8px;font-size:16px;font-weight:600;margin-bottom:12px;">
            ⚠️ You have used <strong>{usage} of {limit}</strong> questions
            on the <strong>{tier}</strong> tier ({pct}% used).
            You are approaching your limit — it resets 24 hours after your last login.
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    # SAVE USER MESSAGE
    # -------------------------------
    chat_history.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    # -------------------------------
    # AI RESPONSE
    # -------------------------------
    try:
        response = ask_question(prompt)
    except Exception as e:
        st.error(f"Agent error: {e}")
        st.stop()

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
    # SAVE CHAT & UPDATE USAGE
    # -------------------------------
    chat_history.append({"role": "assistant", "content": str(response)})
    save_chat(user, chat_history)
    increment_usage(user)
