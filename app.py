import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

# Laad omgevingsvariabelen
load_dotenv()

# Configureer de Google API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Google API sleutel niet gevonden. Zorg ervoor dat je een .env bestand hebt met GOOGLE_API_KEY.")
    st.stop()

genai.configure(api_key=api_key)

def get_pdf_text(pdf_docs):
    """Haal tekst uit de PDF-documenten."""
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def get_text_chunks(text):
    """Splits de tekst in kleinere stukken voor een betere context."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    """Maak een vector store van de tekstchunks en sla deze lokaal op."""
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local("faiss_index")
        return vector_store
    except Exception as e:
        st.error(f"Fout bij het maken van de vector store: {e}")
        return None

def create_conversational_chain():
    """
    Creëer een ConversationalRetrievalChain met geheugen en een aangepast prompttemplate.
    Deze chain haalt relevante context op uit de FAISS-index en houdt de gespreksgeschiedenis bij.
    """
    # Gemini model. Hogere temperature voor creatievere antwoorden
    llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash-001", temperature=0.7)

    # Laad de FAISS-index met de juiste embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

    # Creëer een conversatiegeheugen dat de gespreksgeschiedenis bijhoudt
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    #  Prompttemplate dat de chatbot instrueert om uitgebreid te antwoorden
    custom_prompt = """
    Je bent een behulpzame AI-assistent die een natuurlijk en interactief gesprek voert over de inhoud van de PDF-documenten.
    Zorg ervoor dat je uitgebreide en gedetailleerde antwoorden geeft wanneer de gebruiker hierom vraagt.
    Stimuleer vervolgvragen door af te sluiten met vragen als: "Is er nog iets anders waar je meer over wilt weten?"

    Gespreksgeschiedenis:
    {chat_history}

    Context:
    {context}

    Vraag:
    {question}

    Geef een uitgebreid en accuraat antwoord:
    """

    prompt_template = PromptTemplate(
        template=custom_prompt,
        input_variables=["chat_history", "context", "question"]
    )

    # Maak de ConversationalRetrievalChain aan met het FAISS-retriever, geheugen en aangepaste prompt
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt_template},
        verbose=True
    )
    return qa_chain

def process_user_input(user_question):
    """Verwerk de gebruikersvraag en genereer een antwoord met behulp van de conversational chain."""
    try:
        if "conversation_chain" not in st.session_state:
            st.session_state.conversation_chain = create_conversational_chain()

        chain = st.session_state.conversation_chain

        # Voer de vraag in de chain in; de chain combineert vraag, context en gespreksgeschiedenis
        result = chain({"question": user_question})
        answer = result["answer"]

        # Voeg de vraag en het antwoord toe aan de gespreksgeschiedenis
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

        return answer
    except Exception as e:
        st.error(f"Fout bij het verwerken van je vraag: {e}")
        return f"Er is een fout opgetreden: {str(e)}"

def display_chat_history():
    """Toon de gespreksgeschiedenis in de interface."""
    if "chat_history" in st.session_state:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'**👤 Jij:** {message["content"]}')
            else:
                st.markdown(f'**🤖 Chatbot:** {message["content"]}')

def initialize_chat():
    """Initialiseer de gespreksgeschiedenis en reset de conversational chain indien nodig."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "conversation_chain" in st.session_state and st.session_state.conversation_chain is None:
        del st.session_state.conversation_chain

def main():
    """Hoofdfunctie voor de Streamlit-applicatie."""
    st.set_page_config(page_title="PDF Chat")
    st.header("Gemini-Powered PDF Chatbot")

    # Initialiseer de chat
    initialize_chat()

    # Sidebar voor bestandsupload en verwerking
    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader(
            "Upload je PDF-bestanden en klik op 'Verwerken'",
            accept_multiple_files=True
        )

        if st.button("Verwerken"):
            if not pdf_docs:
                st.error("Upload eerst PDF-bestanden.")
            else:
                with st.spinner("Bezig met verwerken..."):
                    raw_text = get_pdf_text(pdf_docs)
                    if not raw_text:
                        st.error("Geen tekst gevonden in de PDF-bestanden.")
                        st.stop()

                    text_chunks = get_text_chunks(raw_text)
                    if not text_chunks:
                        st.error("Probleem bij het splitsen van de tekst.")
                        st.stop()

                    vector_store = get_vector_store(text_chunks)
                    if vector_store:
                        st.success("PDF-bestanden succesvol verwerkt!")
                        st.session_state.chat_history = []
                        if "conversation_chain" in st.session_state:
                            del st.session_state.conversation_chain
                    else:
                        st.error("Er is een probleem opgetreden bij het verwerken van de PDFs.")

        if st.button("Wis Gespreksgeschiedenis"):
            st.session_state.chat_history = []
            if "conversation_chain" in st.session_state:
                del st.session_state.conversation_chain
            st.success("Gespreksgeschiedenis is gewist!")

    # Toon de gespreksgeschiedenis
    st.subheader("Gesprek:")
    display_chat_history()

    # Formulier voor het invoeren van de vraag
    with st.form(key="question_form", clear_on_submit=True):
        user_question = st.text_input("Stel een vraag over je PDF-bestanden:")
        submit_button = st.form_submit_button("Verstuur vraag")

    if submit_button and user_question:
        # Verwerk de vraag en toon het antwoord meteen
        st.session_state.current_question = user_question
        answer = process_user_input(user_question)

        # Toon het nieuwste antwoord direct onder het formulier
        st.markdown(f"**🤖 Chatbot:** {answer}")

if __name__ == "__main__":
    main()
