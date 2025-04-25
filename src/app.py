import streamlit as st
from pinecone import Pinecone, ServerlessSpec
import time
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI  # Import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Pinecone setup
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
spec = ServerlessSpec(cloud="aws", region="us-east-1")
index_name = 'product-catalog-index'
myindex = pc.Index(index_name)
time.sleep(1)

# Embedding model (for LangChain)
embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vectorstore = PineconeVectorStore(index=myindex, embedding=embed_model, text_key="text")

# Session state to track chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# System message defining the chatbot behavior
system_message = (
    "You are a helpful and respectful shop assistant who answers product-related queries. "
    "If a query lacks a direct answer (e.g. durability), generate a response based on related features. "
    "Politely inform the user if the question is unrelated to the shop. "
    "Use a conversational tone, not too formal."
)

# Function to query Gemini 2.0 Flash using `langchain-google-genai`
def generate_answer_google_genai(system_message, chat_history, prompt):
    # Configure the Google API client
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-001", 
        temperature=0.7,
        max_tokens=1024,
        timeout=None,
        max_retries=2,
    )

    # Prepare the full prompt for the model
    full_prompt = f"{system_message}\n\n" + "\n".join(chat_history + [f"User: {prompt}"]) + "\nAssistant:"
    
    # Generate a response using the model
    response = llm.invoke([("system", system_message), ("human", prompt)])
    answer = response.content  # Extract the response text
    
    # Append user and assistant messages to chat history
    chat_history.append(f"User: {prompt}")
    chat_history.append(f"Assistant: {answer}")
    
    return answer

# Function to search for relevant product passage in the Pinecone vectorstore
def get_relevant_passage(query, vectorstore):
    results = vectorstore.similarity_search(query, k=1)
    if results:
        metadata = results[0].metadata
        context = (
            f"📦 Product: {metadata.get('ProductName', 'N/A')}\n"
            f"🎨 Color: {metadata.get('Color', 'N/A')}\n"
            f"💾 Memory: {metadata.get('Memory', 'N/A')}\n"
            f"💸 Price: {metadata.get('Price', 'N/A')}\n"
            f"📋 Status: {metadata.get('Status', 'N/A')}\n"
            f"⚙️ Attributes: {metadata.get('Attributes', 'N/A')}"
        )
        return context
    return "No relevant product found."

# Function to create a prompt for the chatbot
def make_rag_prompt(query, context):
    return f"Query: {query}\n\nContext:\n{context}\n\nAnswer:"

# Streamlit UI
st.title("🛒 Shop Assistant Chatbot")
query = st.text_input("❓ Ask a question about a product:")

if st.button("🔍 Get Answer"):
    if query.strip():
        context = get_relevant_passage(query, vectorstore)
        prompt = make_rag_prompt(query, context)
        
        # Call the function using `google-genai` SDK for direct responses
        answer = generate_answer_google_genai(system_message, st.session_state.chat_history, prompt)

        st.markdown(f"### 💬 Answer:\n{answer}")
        with st.expander("🕘 Chat History"):
            for chat in st.session_state.chat_history:
                st.text(chat)
