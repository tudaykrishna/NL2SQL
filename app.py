import streamlit as st
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/chat"

st.title("NL2SQL Interface")
st.caption("Chat with your database using natural language → SQL")

# ---------- Chat history ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------- Helper functions ----------
def call_nl2sql_api(message: str) -> str:
    """Call your FastAPI NL2SQL endpoint and return the final_response text."""
    payload = {
        "message": message,
        "last_query": "",
        "last_sql": "",
        "last_result_summary": "",
        "db_dialect": "sqlite",
        "max_rows": 1000,
        "max_eval_retries": 3,
        "max_debug_retries": 3,
    }

    response = requests.post(API_URL, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"Request failed with status code {response.status_code}: {response.text}"
        )

    data2 = response.json()

    # Your backend seems to return a JSON-encoded string, so handle both cases
    if isinstance(data2, str):
        obj = json.loads(data2)
    else:
        obj = data2

    return obj.get("final_response", "No 'final_response' field found in API response.")


def stream_text(text: str):
    """Stream the response word-by-word to mimic typing."""
    for word in text.split():
        yield word + " "
        time.sleep(0.02)


# ---------- Chat input ----------

prompt = st.chat_input("Enter your question / request for SQL:")
if prompt:
    
    # 1. Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Show user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Call backend and show assistant response
    try:
        full_response = call_nl2sql_api(prompt)

        with st.chat_message("assistant"):
            # Stream the text like the Streamlit docs example
            st.write_stream(stream_text(full_response))

        # 4. Save assistant message to history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

    except Exception as e:
        error_msg = f"⚠️ Error contacting NL2SQL API:\n\n{e}"
        with st.chat_message("assistant"):
            st.markdown(error_msg)

        st.session_state.messages.append(
            {"role": "assistant", "content": error_msg}
        )
