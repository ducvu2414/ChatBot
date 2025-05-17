from langchain.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
import chromadb
import re
import os
import json
from dotenv import load_dotenv
load_dotenv()

chroma_client = chromadb.PersistentClient(path="./chroma_db")

embedding_model = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return embedding_model

vectorstore = Chroma(
    collection_name="products",
    embedding_function=get_embedding_model(),
    client=chroma_client
)

# GROQ LLM for extracting filters
llm = ChatGroq(
    model_name="llama3-70b-8192",
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY")
)

filter_system = SystemMessage(content="""
Bạn là công cụ phân tích tiêu chí lọc sản phẩm. Dựa vào câu hỏi bằng tiếng Việt, hãy trả về JSON chứa các trường sau:
- price_min (số hoặc null)
- price_max (số hoặc null)
- colors (mảng tiếng Anh: ví dụ ["black", "white"])
- memories (mảng như ["4GB", "8GB"])
- status ("AVAILABLE" hoặc null)
- attributes (mảng từ khóa như ["5G", "AMOLED"])
Chỉ trả về JSON, không thêm lời giải thích.
""")

def extract_filters(query: str) -> dict:
    from langchain_core.messages import HumanMessage
    resp = llm.invoke([filter_system, HumanMessage(content=query)])

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
        content = content.replace("\n", "")
        result = json.loads(content)
        return {**default, **result}
    except Exception as e:
        print("❌ JSON parse error:", e)
        return default

def search_product_context(query: str) -> str:
    filters = extract_filters(query)
    results = vectorstore.similarity_search(query, k=15)
    if not results:
        return "Không tìm thấy sản phẩm nào phù hợp."

    all_products = []
    seen = set()

    for doc in results:
        m = doc.metadata
        name = m.get("ProductName", "Không rõ")
        if name in seen:
            continue

        try:
            price = float(m.get("Price", 0))
        except:
            price = 0

        color = m.get("Color", "").lower()
        memory = m.get("Memory", "")
        status = m.get("Status", "").upper()
        attrs = m.get("Attributes", "").lower()

        if filters["price_min"] and price < filters["price_min"]:
            continue
        if filters["price_max"] and price > filters["price_max"]:
            continue
        if filters["colors"] and all(c not in color for c in filters["colors"]):
            continue
        if filters["memories"] and memory not in filters["memories"]:
            continue
        if filters["status"] and status != filters["status"]:
            continue
        if filters["attributes"] and all(a not in attrs for a in filters["attributes"]):
            continue

        seen.add(name)

        lines = [
            f"📦 Tên sản phẩm: {name}  \n",
            f"🎨 Màu: {m.get('Color', 'Không rõ')}  \n",
            f"💾 RAM: {m.get('Memory', 'Không rõ')}  \n",
            f"💸 Giá: {m.get('Price', 'Không rõ')}  \n",
            f"📋 Trạng thái: {m.get('Status', 'Không rõ')}  \n",
            "⚙️ Thuộc tính khác:"
        ]

        if isinstance(attrs, str):
            attr_lines = [f"- {item.strip()}" for item in re.split(r';', attrs) if item.strip()]
        else:
            attr_lines = []

        attr_text = "\n".join(attr_lines)
        all_products.append("\n".join(lines) + "\n" + attr_text + "\n---")

    if not all_products:
        return "Không tìm thấy sản phẩm nào thỏa mãn tất cả tiêu chí của bạn."

    return "\n".join(all_products)
