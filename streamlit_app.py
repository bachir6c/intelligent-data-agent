import sys
from pathlib import Path
import streamlit as st
import re
from pathlib import Path

def extract_chart_path(text):
    match = re.search(r"([A-Za-z]:\\[^\n`]+\.png)", text)
    if match:
        return match.group(1).strip()
    return None

# Permet d'importer les fichiers présents dans src/
SRC_PATH = Path(__file__).parent / "src"
sys.path.append(str(SRC_PATH))

from agent import run_agent
from agent_service import query_agent


st.set_page_config(
    page_title="Intelligent Data Agent",
    page_icon="🤖",
    layout="centered"
)


st.title("Intelligent Data Analysis Agent")

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


# Zone de saisie
question = st.chat_input(
    "Ask a question about the database..."
)


if question:

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
                result = query_agent(question)

                answer = result["answer"]
                chart_path = result["chart_path"]

                st.markdown(answer)

                if chart_path:
                    st.image(
                        chart_path,
                        caption="Generated chart",
                        use_container_width=True
                    )

                if isinstance(result, dict):
                    answer = result.get("answer", "")
                else:
                    answer = str(result)

                st.markdown(answer)

                chart_path = extract_chart_path(answer)

                if chart_path and Path(chart_path).exists():
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
        "content": answer
    })