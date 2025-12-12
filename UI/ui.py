import streamlit as st
import requests
import json
import time
from typing import Generator

# -------------------- Configuration --------------------
API_URL = "http://127.0.0.1:8000/api/chat"
# --------------------------------------------------------

st.set_page_config(page_title="NL2SQL Interface", layout="wide")

st.title("NL2SQL Interface")
st.caption("Chat with your database using natural language → SQL")

# --------------------------------------------------------
# SESSION STATE INIT
# --------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_list" not in st.session_state:
    st.session_state.user_list = ["User1", "User2"]

# transient index used to select newly added user
if "select_index" not in st.session_state:
    st.session_state.select_index = None

# --------------------------------------------------------
# SIDEBAR
# --------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("### Users")

    # Decide the index to preselect
    preselect_index = (
        st.session_state.select_index
        if isinstance(st.session_state.select_index, int)
        else 0
    )

    # user dropdown
    user_option = st.selectbox(
        "Select User",
        st.session_state.user_list,
        index=preselect_index,
        key="selected_user"
    )

    # clear transient index
    if st.session_state.select_index is not None:
        st.session_state.select_index = None

    st.markdown("---")

    # Add User
    st.subheader("Add New User")
    new_user_input = st.text_input("Enter new username")

    if st.button("Add User"):
        new_user = new_user_input.strip()

        if new_user == "":
            st.error("Please enter a valid username.")
        else:
            if new_user in st.session_state.user_list:
                st.warning("User already exists.")
            else:
                st.session_state.user_list.append(new_user)
                st.session_state.select_index = len(st.session_state.user_list) - 1
                st.success(f"User '{new_user}' added and selected.")
                st.rerun()

    st.markdown("---")

    # Clear chat
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.success("Chat cleared.")
        st.rerun()

# --------------------------------------------------------
# CHAT HISTORY
# --------------------------------------------------------
for message in st.session_state.messages:
    sender = message.get("user", "User")
    role = message.get("role", "user")

    with st.chat_message(role):
        st.markdown(f"**{sender}:** {message['content']}")

# --------------------------------------------------------
# API CALL
# --------------------------------------------------------
def call_nl2sql_api(message: str, user: str) -> str:
    payload = {
        "message": message,
        "user": user,
        "last_query": "",
        "last_sql": "",
        "last_result_summary": "",
        "db_dialect": "sqlite",
        "max_rows": 1000,
        "max_eval_retries": 3,
        "max_debug_retries": 3,
    }

    response = requests.post(API_URL, json=payload, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"API Error {response.status_code}: {response.text}")

    data = response.json()
    obj = json.loads(data) if isinstance(data, str) else data
    return obj.get("final_response", "(No response from API)")

def stream_text_generator(text: str):
    for word in text.split():
        yield word + " "
        time.sleep(0.02)

# --------------------------------------------------------
# CHAT INPUT
# --------------------------------------------------------
prompt = st.chat_input("Enter your question / request for SQL:")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "user": user_option,
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(f"**{user_option}:** {prompt}")

    try:
        full_response = call_nl2sql_api(prompt, user_option)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            stream_accum = ""

            for chunk in stream_text_generator(full_response):
                stream_accum += chunk
                placeholder.markdown(stream_accum)

        st.session_state.messages.append({
            "role": "assistant",
            "user": "Assistant",
            "content": full_response
        })

    except Exception as e:
        error_msg = f"⚠️ API Error:\n{e}"

        with st.chat_message("assistant"):
            st.markdown(error_msg)

        st.session_state.messages.append({
            "role": "assistant",
            "user": "Assistant",
            "content": error_msg
        })
        