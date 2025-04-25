import streamlit as st
from pinecone import Pinecone, ServerlessSpec
import time
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Pinecone setup
api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=api_key)

spec = ServerlessSpec(cloud="aws", region="us-east-1")
index_name = 'product-catalog-index'
myindex = pc.Index(index_name)
time.sleep(1)

# Embedding model
embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Connect vector store
vectorstore = PineconeVectorStore(
    index=myindex,
    embedding=embed_model,
    text_key=None  # <-- Không cần chỉ định nếu dùng metadata
)

# Khởi tạo chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Định nghĩa hệ thống hướng dẫn cho chatbot
system_message = (
    "You are a helpful and respectful shop assistant who answers product-related queries. "
    "If a query lacks a direct answer (e.g. durability), generate a response based on related features. "
    "Politely inform the user if the question is unrelated to the shop. "
    "Use a conversational tone, avoid sounding robotic or overly formal."
)

# Sinh câu trả lời từ Gemini
def generate_answer(system_message, chat_history, prompt):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-pro')

    chat_history.append(f"User: {prompt}")
    full_prompt = f"{system_message}\n\n" + "\n".join(chat_history) + "\nAssistant:"
    response = model.generate_content(full_prompt).text
    chat_history.append(f"Assistant: {response}")
    return response

# Lấy thông tin sản phẩm liên quan từ vectorstore
def get_relevant_passage(query, vectorstore):
    results = vectorstore.similarity_search(query, k=1)
    if results:
        metadata = results[0].metadata
        context = (
            f"📦 Product Name: {metadata.get('ProductName', 'N/A')}\n"
            f"🎨 Color: {metadata.get('Color', 'N/A')}\n"
            f"💾 Memory: {metadata.get('Memory', 'N/A')}\n"
            f"💸 Price: {metadata.get('Price', 'N/A')}\n"
            f"📋 Status: {metadata.get('Status', 'N/A')}\n"
            f"⚙️ Attributes: {metadata.get('Attributes', 'N/A')}"
        )
        return context
    return "No relevant product found."

# Tạo prompt RAG
def make_rag_prompt(query, context):
    return f"Query: {query}\n\nContext:\n{context}\n\nAnswer:"

# Giao diện Streamlit
st.title("🛍️ Shop Assistant Chatbot")

query = st.text_input("Ask your product question:")

if st.button("Get Answer"):
    if query.strip():
        relevant_text = get_relevant_passage(query, vectorstore)
        prompt = make_rag_prompt(query, relevant_text)
        answer = generate_answer(system_message, st.session_state.chat_history, prompt)

        st.markdown(f"### 💬 Answer:\n{answer}")
        with st.expander("🕘 Chat History"):
            for chat in st.session_state.chat_history:
                st.text(chat)
