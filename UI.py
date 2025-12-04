import streamlit as st
import requests
import json

url = "http://127.0.0.1:8000/chat"

st.title("NL2SQL Interface")
st.write("This is a simple UI for interacting with the NL2SQL agent.")
user_input = st.text_input("Enter your SQL query:")

if st.button("Submit"):
    
    
    data = {
  "message": f"{user_input}",
  "last_query": "",
  "last_sql": "",
  "last_result_summary": "",
  "db_dialect": "sqlite",
  "max_rows": 1000,
  "max_eval_retries": 3,
  "max_debug_retries": 3
}
    response = requests.post(url, json=data)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data2 = response.json()
        # st.write(data2)

        obj = json.loads(data2)

        st.write(obj["final_response"])
        # print("Data received:")
        # print(data2)
    else:
        st.write(f"Request failed with status code: {response.status_code}")
        

