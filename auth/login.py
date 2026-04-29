import streamlit as st
from datetime import datetime, timedelta
from auth.bigquery_auth import verify_user
from auth.users import (
    get_or_create_user, reset_usage, should_reset_usage,
    update_last_login, get_usage, get_last_login, get_last_queried,
)
from auth.rbac import get_usage_limit


def login_signup():
    st.sidebar.title("🔐 Login")

    if "user" in st.session_state:
        tier = st.session_state.get("tier", "free")
        user_id = st.session_state.user
        usage = get_usage(user_id)
        limit = get_usage_limit(tier)
        last_login_str = get_last_login(user_id)

        st.sidebar.markdown("---")
        st.sidebar.write(f"**User:** {user_id}")
        st.sidebar.write(f"**Tier:** {tier}")

        if limit is None:
            st.sidebar.write("**Queries remaining:** Unlimited")
        else:
            remaining = max(0, limit - usage)
            st.sidebar.write(f"**Queries remaining:** {remaining} / {limit}")
            from auth.rbac import is_near_limit
            if remaining > 0 and is_near_limit(usage, tier):
                pct = int(usage / limit * 100)
                st.sidebar.warning(f"⚠️ {pct}% of your {tier} limit used ({usage}/{limit}). Approaching limit!")

        if last_login_str:
            login_dt = datetime.fromisoformat(last_login_str)
            st.sidebar.write(f"**Last login:** {login_dt.strftime('%d %b %Y, %H:%M')}")

        if limit is not None:
            last_queried_str = get_last_queried(user_id)
            if last_queried_str:
                reset_at = datetime.fromisoformat(last_queried_str) + timedelta(hours=24)
                st.sidebar.write(f"**Limit resets at:** {reset_at.strftime('%d %b %Y, %H:%M')}")
            else:
                st.sidebar.write("**Limit resets at:** no queries yet")

        st.sidebar.markdown("---")
        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.rerun()
        return

    user_id = st.sidebar.text_input("User ID")
    email = st.sidebar.text_input("Email Address")

    if st.sidebar.button("Login"):
        if not user_id or not email:
            st.sidebar.error("Please enter both User ID and email.")
            return

        user = verify_user(user_id, email)
        if user:
            st.session_state.user = user["user_id"]
            st.session_state.tier = user["tier"]
            get_or_create_user(user["user_id"])

            if should_reset_usage(user["user_id"]):
                reset_usage(user["user_id"])

            update_last_login(user["user_id"])
            st.rerun()
        else:
            st.sidebar.error("No account found with that User ID and email.")
