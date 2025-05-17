# import streamlit as st
# from database import search_product_context
# from ai_function import shopbot_ai

# st.set_page_config(page_title="Shop Assistant Chatbot", page_icon="🛒")

# st.title("🛒 Shop Assistant Chatbot")
# query = st.text_input("❓ Ask a question about a product:")

# if st.button("🔍 Get Answer"):
#     if query.strip():
#         context = search_product_context(query)

#         response = shopbot_ai(user_query=query, context=context)

#         st.markdown("### 💬 Answer:")
#         formatted_response = response.replace("\n", "  \n") 
#         st.markdown(formatted_response, unsafe_allow_html=True)

import streamlit as st
from streamlit_chat import message
import random
from chatbot import shop_chatbot


st.set_page_config(page_title='🤖 Shop Assistant Chatbot', layout='centered', page_icon='🛒')
st.title("🤖 Shop Assistant Chatbot Chat AI")

# adding session state to each user session
session_id = random.randint(0, 100000)
# adding session_id to session state
if "session_id" not in st.session_state:
    st.session_state.session_id = session_id

# initial message
INIT_MESSAGE = {"role": "assistant",
                "content": "Hello! I am your Shop Assistant Chat Agent, I will help answer all questions you might have about Phone."}


if "messages" not in st.session_state:
        st.session_state.messages = [INIT_MESSAGE]

def generate_response(input_text):
    output = shop_chatbot(user_query=input_text)
    return output

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
user_input = st.chat_input(placeholder="Your message ....", key="input")

# display user input
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    user_message = st.chat_message("user")
    user_message.write(user_input)

# Generate response
if st.session_state.messages[-1]["role"] != "assistant":
    response = generate_response(user_input)
    st.session_state.messages.append({"role": "assistant", "content": response})
    assistant_message = st.chat_message("assistant")

    formatted = response.replace("\n", "  \n")
    assistant_message.markdown(formatted)
