from database import search_product_context
from ai_function import shopbot_ai

def shop_chatbot(user_query: str) -> str:
    context = search_product_context(user_query)
    print("Context: ", context)
    answer = shopbot_ai(user_query=user_query, context=context)
    return answer
