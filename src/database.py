# import os
# from dotenv import load_dotenv
# from langchain_pinecone import PineconeVectorStore
# from langchain_huggingface import HuggingFaceEmbeddings
# from pinecone import Pinecone, ServerlessSpec


# load_dotenv()

# pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
# index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
# spec = ServerlessSpec(cloud="aws", region="us-east-1")

# embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# vectorstore = PineconeVectorStore(index=index, embedding=embedding_model, text_key="text")


# def search_product_context(query: str) -> str:
#     results = vectorstore.similarity_search(query, k=10)
#     if not results:
#         return "Không tìm thấy sản phẩm nào phù hợp."

#     all_products = []
#     for doc in results:
#         m = doc.metadata
#         attributes = m.get('Attributes')
#         if isinstance(attributes, dict):
#             attr_lines = [f"- {key}: {value}" for key, value in attributes.items()]
#         elif isinstance(attributes, str):
#             import re
#             attr_lines = [f"- {item.strip()}" for item in re.split(r',', attributes) if ':' in item]
#         else:
#             attr_lines = []

#         attr_text = "\n".join(attr_lines)

#         product = (
#             f"ProductName: {m.get('ProductName', 'Không rõ')}\n"
#             f"Color: {m.get('Color', 'Không rõ')}\n"
#             f"Memory: {m.get('Memory', 'Không rõ')}\n"
#             f"Price: {m.get('Price', 'Không rõ')}\n"
#             f"Status: {m.get('Status', 'Không rõ')}\n"
#             f"Attributes:\n{attr_text}\n"
#             f"---"
#         )
#         all_products.append(product)

#     for i in range(len(all_products)):
#         print(f"Product {i+1}:\n{all_products[i]}\n")
#     return "\n".join(all_products)

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import re
import os
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec


load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
spec = ServerlessSpec(cloud="aws", region="us-east-1")

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

vectorstore = PineconeVectorStore(index=index, embedding=embedding_model, text_key="text")
filter_llm = ChatGroq(model_name="llama3-70b-8192", temperature=0.0)
filter_system = SystemMessage(content="""
You are a Vietnamese query analyzer and translator.

Input: a Vietnamese sentence describing phone search criteria.
Output: a JSON object in English containing fields:
- price_min (number, unit: VND, null if not mentioned)
- price_max (number, unit: VND, null if not mentioned)
- colors (array of English color strings, e.g. ["black", "white"], [] if none)
- memories (array of strings like "8GB", "12GB", [] if none)
- status (string, e.g. "AVAILABLE" or null if not mentioned)
- attributes (array of keywords/features like "OLED", "5G", [] if none)

❗ All values must be translated to English if originally in Vietnamese.
❗ Only return valid JSON. Do NOT add explanations or comments.

Example:
Input: "Điện thoại từ 10 đến 20 triệu, màu đen, RAM 8GB và 12GB, hàng mới, hỗ trợ 5G"
Output:
{
  "price_min": 10000000,
  "price_max": 20000000,
  "colors": ["black"],
  "memories": ["8GB", "12GB"],
  "status": "AVAILABLE",
  "attributes": ["5G"]
}
""")


def extract_filters(query: str) -> dict:
    resp = filter_llm.invoke([filter_system, HumanMessage(content=query)])
    import json

    default = {
        "price_min": None,
        "price_max": None,
        "colors": [],
        "memories": [],
        "status": None,
        "attributes": []
    }

    try:
        content = resp.content.strip()

        if not content.startswith("{"):
            content = content[content.find("{"):] 
        content = content.replace("\n", "").replace("},", "}")

        result = json.loads(content)
        return {**default, **result}
    except Exception as e:
        print("❌ Lỗi khi parse JSON từ LLM:", e)
        print("⛔ Output LLM gây lỗi:\n", resp.content)
        return default

def search_product_context(query: str) -> str:
    
    filters = extract_filters(query)
    print("📥 Filters:", filters)

    results = vectorstore.similarity_search(query, k=10)
    if not results:
        return "Không tìm thấy sản phẩm nào phù hợp."

    out, seen = [], set()
    for doc in results:
        m = doc.metadata
        price = float(m.get('Price', 0))
        color = m.get('Color', '').lower()
        mem   = m.get('Memory', '')
        status= m.get('Status', '').upper()
        attrs = m.get('Attributes', '').lower()
        name  = m.get('ProductName', '').strip()


        # if filters["price_min"] and price < filters["price_min"]:
        #     continue
        # if filters["price_max"] and price > filters["price_max"]:
        #     continue
        # if filters["colors"] and all(c not in color for c in filters["colors"]):
        #     continue
        # if filters["memories"] and mem not in filters["memories"]:
        #     continue
        # if filters["status"] and status != filters["status"]:
        #     continue
        # if filters["attributes"] and all(a not in attrs for a in filters["attributes"]):
        #     continue

        # if name in seen:
        #     continue
        # seen.add(name)

        if not (
            (not filters["price_min"] or price >= filters["price_min"]) and
            (not filters["price_max"] or price <= filters["price_max"]) and
            (not filters["colors"] or any(c in color for c in filters["colors"])) and
            (not filters["memories"] or mem in filters["memories"]) and
            (not filters["status"] or status == filters["status"]) and
            (not filters["attributes"] or any(a in attrs for a in filters["attributes"])) and
            (name not in seen)
        ):
            continue


        lines = [
            f"📦 Tên sản phẩm: {name}  \n",
            f"🎨 Màu: {m.get('Color', 'Không rõ')}  \n",
            f"💾 RAM: {m.get('Memory', 'Không rõ')}  \n",
            f"💸 Giá: {m.get('Price', 'Không rõ')}  \n",
            f"📋 Trạng thái: {m.get('Status', 'Không rõ')}  \n",
            "⚙️ Thuộc tính khác:"
        ]


        attributes = m.get('Attributes')
        if isinstance(attributes, dict):
            attr_lines = [f"- {key}: {value}" for key, value in attributes.items()]
        elif isinstance(attributes, str):
            import re
            attr_lines = [f"- {item.strip()}" for item in re.split(r',|;', attributes) if ':' in item]
        else:
            attr_lines = []

        attr_text = " \n".join(attr_lines)
        out.append("  \n".join(lines) + "  \n" + attr_text + "  \n---")


    return "\n".join(out)

