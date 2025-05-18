import sys
import importlib

import pysqlite3
sys.modules["sqlite3"] = pysqlite3
importlib.reload(pysqlite3)

import os
import sys
import random
import traceback
import subprocess
import pandas as pd
import streamlit as st
from streamlit_chat import message
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb
from chatbot import shop_chatbot



# ✅ Cấu hình giao diện Streamlit
st.set_page_config(page_title='🤖 Shop Assistant Chatbot', layout='centered', page_icon='🛒')
st.title("🛒 Shop Assistant Chatbot")

# ✅ Khởi tạo Chroma client
CHROMA_DB_PATH = "/tmp/chroma_db"
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# ✅ Hàm sync dữ liệu từ CSV vào ChromaDB
def sync_chroma_data():
    try:
        st.info("🚀 Bắt đầu sync dữ liệu vào ChromaDB...")

        csv_path = "product_data.csv"
        if not os.path.exists(csv_path):
            st.error(f"❌ Không tìm thấy file {csv_path}")
            st.stop()

        st.write("🔧 Khởi tạo embedding và Chroma client...")
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

        vectorstore = Chroma(
            collection_name="products",
            embedding_function=embedding_model,
            client=client
        )

        st.write("✨ Đang đọc file CSV...")
        df = pd.read_csv(csv_path)

        st.write("📊 Đang tạo embedding và metadata...")
        documents, metadatas = [], []
        for _, row in df.iterrows():
            name = row['product_variant_name']
            color = row['color_name']
            memory = row['memory_name']
            price = row.get('price', 'Không rõ')
            status = row['product_variant_status']
            attributes = row['attributes']

            text = f"{name}. Màu: {color}. RAM: {memory}. Giá: {price}. Trạng thái: {status}. Thuộc tính: {attributes}"
            documents.append(text)
            metadatas.append({
                "ProductName": name,
                "Color": color,
                "Memory": memory,
                "Price": price,
                "Status": status,
                "Attributes": attributes,
                "text": text
            })

        st.write("💾 Đang thêm vào vectorstore...")
        vectorstore.add_texts(texts=documents, metadatas=metadatas)

        st.success("✅ Đã sync xong vào ChromaDB!")

    except Exception:
        st.error("❌ Lỗi khi sync dữ liệu vào ChromaDB:")
        st.text(traceback.format_exc())
        st.stop()

# ✅ Kiểm tra nếu collection chưa tồn tại
collections = [col.name for col in client.list_collections()]
if "products" not in collections:
    with st.spinner("🔄 Initializing product database... (one-time setup)"):
        sync_chroma_data()

# ✅ Quản lý session
session_id = random.randint(0, 100000)
if "session_id" not in st.session_state:
    st.session_state.session_id = session_id

# ✅ Tin nhắn khởi tạo
INIT_MESSAGE = {
    "role": "assistant",
    "content": "Hello! I am your Shop Assistant. Ask me anything about our phones 📱!"
}
if "messages" not in st.session_state:
    st.session_state.messages = [INIT_MESSAGE]

# ✅ Hàm gọi chatbot logic
def generate_response(input_text):
    return shop_chatbot(user_query=input_text)

# ✅ Hiển thị tin nhắn
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"].replace("\n", "  \n"), unsafe_allow_html=True)

# ✅ Nhận input người dùng
user_input = st.chat_input(placeholder="Ask me about a phone...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = shop_chatbot(user_input)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(response.replace("\n", "  \n"))
