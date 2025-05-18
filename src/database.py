from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
import chromadb
import re
import os
import json
from dotenv import load_dotenv
load_dotenv()

persist_path = "/tmp/chroma_db"
os.makedirs(persist_path, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=persist_path)

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
Bạn là một công cụ phân tích tiêu chí lọc sản phẩm. Dựa trên câu hỏi đầu vào bằng tiếng Việt từ người dùng, hãy trích xuất và trả về kết quả dưới dạng JSON với các trường sau:

- "price_min": số nguyên thể hiện giá thấp nhất, hoặc null nếu không đề cập.
- "price_max": số nguyên thể hiện giá cao nhất, hoặc null nếu không đề cập.
- "colors": mảng các màu (bằng tiếng Anh, ví dụ: ["black", "white"]), hoặc mảng rỗng nếu không đề cập.
- "memories": mảng các tùy chọn bộ nhớ trong (ví dụ: ["64GB", "128GB"]), hoặc mảng rỗng nếu không đề cập. Nếu người dùng chỉ nhắc đến dung lượng như "128GB", "256GB" mà không ghi rõ là ROM hoặc bộ nhớ trong, vẫn hiểu là "memories".
- "ram": mảng các tùy chọn RAM (ví dụ: ["4GB", "8GB"]), hoặc mảng rỗng nếu không đề cập. Nếu người dùng chỉ nhắc đến giá trị như "4GB", "8GB" mà không ghi rõ là RAM, vẫn hiểu là "ram".
- "status": "AVAILABLE" nếu người dùng yêu cầu sản phẩm còn hàng, hoặc null nếu không rõ. Nếu người dùng chỉ nhắc đến tình trạng sản phẩm (ví dụ: "còn hàng", "có sẵn") mà không ghi rõ trường, vẫn hiểu là "status".
- "attributes": mảng các từ khóa đặc điểm nổi bật của sản phẩm (ví dụ: ["5G", "AMOLED", "Snapdragon", "eSIM"]), hoặc mảng rỗng nếu không đề cập. Nếu người dùng nhắc đến các đặc điểm nổi bật mà không chỉ rõ đó là thuộc tính, vẫn hiểu là "attributes".

Chỉ trả về đúng định dạng JSON, không thêm bất kỳ lời giải thích, tiêu đề hoặc chú thích nào khác.
""")



def extract_filters(query: str) -> dict:
    from langchain_core.messages import HumanMessage
    resp = llm.invoke([filter_system, HumanMessage(content=query)])

    default = {
        "price_min": None,
        "price_max": None,
        "colors": [],
        "memories": [],
        "ram": [],
        "status": None,
        "attributes": []
    }

    try:
        content = resp.content.strip()
        print("🧠 Raw LLM output:", content)

        content = re.sub(r'\](\s*])', ']', content)
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*\]', ']', content)

        match = re.search(r'\{.*\}', content, re.DOTALL)
        if not match:
            print("❌ Không tìm thấy đoạn JSON hợp lệ.")
            return default

        json_str = match.group(0)
        result = json.loads(json_str)
        return {**default, **result}

    except Exception as e:
        print("❌ JSON parse error:", e)
        return default

def search_product_context(query: str) -> str:
    filters = extract_filters(query)
    print("Filters: ",filters)
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
        ram = m.get("Memory", "").upper()
        status = m.get("Status", "").upper()
        attrs = m.get("Attributes", "").lower()

        if filters["price_min"] and price < filters["price_min"]:
            continue
        if filters["price_max"] and price > filters["price_max"]:
            continue
        if filters["colors"] and all(c not in color for c in filters["colors"]):
            continue
        # if filters["memories"] and memory not in filters["memories"]:
        #     continue
        if filters["ram"] and ram not in filters["ram"]:
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

    return "\n\n".join(all_products)
