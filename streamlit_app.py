import os
import streamlit as st
import re

def extract_chart_path(text):
    match = re.search(r"([A-Za-z]:\\[^\n`]+\.png)", text)
    if match:
        return match.group(1).strip()
    return None

import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/query")
DOCUMENT_URL = API_URL.rsplit("/", 1)[0] + "/documents"

st.set_page_config(
    page_title="Intelligent Data Agent",
    page_icon="🤖",
    layout="centered"
)


st.title("Intelligent Data Analysis Agent")

with st.sidebar:
    st.header("Reference documents")
    uploaded = st.file_uploader("Add a UTF-8 text or Markdown document (up to 1 MB)",
                                type=["txt", "md"])
    if st.button("Save document", disabled=uploaded is None):
        try:
            if uploaded.size > 1_000_000:
                raise ValueError("Each document must be at most 1 MB.")
            document_response = requests.post(DOCUMENT_URL, json={
                "filename": uploaded.name,
                "content": uploaded.getvalue().decode("utf-8-sig"),
            }, timeout=30)
            if not document_response.ok:
                raise ValueError(document_response.json().get("detail", "Upload failed."))
            st.success("Document saved. You can now ask questions about it.")
        except (ValueError, requests.RequestException) as error:
            st.error(str(error))

st.write(
    "Ask questions about the SQL database in natural language. "
    "The agent can query the database, perform statistical analyses, "
    "detect anomalies and generate visualizations."
)


# Historique de conversation
if "messages" not in st.session_state:
    st.session_state.messages = []


# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("chart_path"):
            st.image(message["chart_path"], caption="Generated chart",
                     use_container_width=True)


# Zone de saisie
question = st.chat_input(
    "Ask a question about the database..."
)


if question:
    chart_path = None

    # Afficher la question
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    # Exécuter l'agent
    with st.chat_message("assistant"):

        with st.spinner("Analyzing..."):

            try:
                response = requests.post(
                    API_URL,
                    json={"question": question},
                    timeout=120
                )

                response.raise_for_status()

                result = response.json()

                answer = result["answer"]
                chart_path = result["chart_path"]

                st.markdown(answer)

                if chart_path:
                    st.image(
                        chart_path,
                        caption="Generated chart",
                        use_container_width=True
                    )

            except Exception as error:
                answer = f"Error: {error}"
                st.error(answer)

    # Sauvegarder la réponse
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "chart_path": chart_path
    })
