import os
import subprocess
import streamlit as st
from streamlit_chat import message
import random
from chatbot import shop_chatbot
import chromadb

# ✅ Streamlit UI setup
st.set_page_config(page_title='🤖 Shop Assistant Chatbot', layout='centered', page_icon='🛒')
st.title("🛒 Shop Assistant Chatbot")

# ✅ Khởi tạo Chroma client
CHROMA_DB_PATH = "/tmp/chroma_db"
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# ✅ Kiểm tra collection 'products' đã tồn tại chưa
collections = [col.name for col in client.list_collections()]
if "products" not in collections:
    with st.spinner("🔄 Initializing product database... (one-time setup)"):
        try:
            # Gọi file sync
            subprocess.run(["python", "src/chroma_sync.py"], check=True)

            # Kiểm tra lại sau khi sync
            collections = [col.name for col in client.list_collections()]
            if "products" not in collections:
                st.error("❌ chroma_sync.py đã chạy nhưng không tạo được collection 'products'.")
                st.stop()

            st.success("✅ Product database initialized.")
        except Exception as e:
            st.error(f"❌ Failed to initialize database: {e}")
            st.stop()

# ✅ Quản lý session_id (mỗi người dùng khác nhau)
session_id = random.randint(0, 100000)
if "session_id" not in st.session_state:
    st.session_state.session_id = session_id

# ✅ Khởi tạo tin nhắn đầu tiên
INIT_MESSAGE = {
    "role": "assistant",
    "content": "Hello! I am your Shop Assistant. Ask me anything about our phones 📱!"
}
if "messages" not in st.session_state:
    st.session_state.messages = [INIT_MESSAGE]

# ✅ Hàm gọi chatbot logic
def generate_response(input_text):
    return shop_chatbot(user_query=input_text)

# ✅ Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"].replace("\n", "  \n"), unsafe_allow_html=True)

# ✅ Nhận tin nhắn người dùng
user_input = st.chat_input(placeholder="Ask me about a phone...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(user_input)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(response.replace("\n", "  \n"))
