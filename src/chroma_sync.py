import traceback
import sys
import os

try:
    import pandas as pd
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    import chromadb

    print("🚀 Bắt đầu sync dữ liệu vào ChromaDB...")

    # ✅ Đảm bảo file CSV tồn tại
    csv_path = "product_data.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"❌ Không tìm thấy file {csv_path}")

    # ✅ Khởi tạo embedding & vectorstore
    print("🔧 Khởi tạo embedding và Chroma client...")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    persist_path = "/tmp/chroma_db"
    os.makedirs(persist_path, exist_ok=True)

    chroma_client = chromadb.PersistentClient(path=persist_path)
    vectorstore = Chroma(
        collection_name="products",
        embedding_function=embedding_model,
        client=chroma_client
    )

    # ✅ Đọc dữ liệu
    print("✨ Đang đọc file CSV...")
    df = pd.read_csv(csv_path)

    print("📊 Đang tạo embedding và metadata...")
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

    print("💾 Đang thêm vào vectorstore...")
    vectorstore.add_texts(texts=documents, metadatas=metadatas)

    print("✅ Đã sync xong vào ChromaDB!")

except Exception:
    print("❌ Lỗi trong chroma_sync.py:")
    traceback.print_exc()
    sys.exit(1)

# import pandas as pd
# from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# import chromadb

# # File dữ liệu
# csv_path = "product_data.csv"

# # Mô hình embedding
# embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
# chroma_client = chromadb.PersistentClient(path="./chroma_db")

# vectorstore = Chroma(
#     collection_name="products",
#     embedding_function=embedding_model,
#     client=chroma_client
# )

# def convert_color(color):
#     if not isinstance(color, str):
#         return "Không rõ"
#     c = color.strip().lower()
#     return {
#         "black": "Đen",
#         "white": "Trắng",
#         "blue": "Xanh",
#         "purple": "Tím",
#         "silver": "Bạc",
#         "green": "Xanh lá",
#         "yellow": "Vàng",
#         "red": "Đỏ",
#     }.get(c, color)


# def convert_status(status):
#     if not isinstance(status, str):
#         return "Không rõ"
#     return {
#         "AVAILABLE": "Còn hàng",
#         "OUT_OF_STOCK": "Hết hàng",
#         "DISCONTINUED": "Ngừng bán"
#     }.get(status.upper(), status)


# print("✨ Đang tải dữ liệu sản phẩm...")
# df = pd.read_csv(csv_path)

# print("📊 Đang xử lý embedding và đưa vào ChromaDB...")
# documents, metadatas = [], []
# for _, row in df.iterrows():
#     name = row['product_variant_name']
#     color_en = str(row['color_name'])
#     color_vi = convert_color(color_en)

#     memory = row['memory_name']
#     price = row.get('price', 'Không rõ')
#     status_en = row['product_variant_status']
#     status_vi = convert_status(status_en)

#     attributes = row['attributes']

#     text = f"{name}. Màu: {color_vi}. RAM: {memory}. Giá: {price}. Trạng thái: {status_vi}. Thuộc tính: {attributes}"
#     documents.append(text)
#     metadatas.append({
#         "ProductName": name,
#         "Color": color_vi,
#         "Memory": memory,
#         "Price": price,
#         "Status": status_vi,
#         "Attributes": attributes,
#         "text": text
#     })

# vectorstore.add_texts(texts=documents, metadatas=metadatas)

# print("✅ Hoàn tất đồng bộ vào ChromaDB!")
