
# 🛒 RAG-powered Shop Assistant Chatbot

Chatbot tư vấn sản phẩm được xây dựng với công nghệ **Retrieval-Augmented Generation (RAG)** sử dụng **LangChain**, **Pinecone**, **Google Gemini** và **Streamlit**.

> ✅ Tích hợp với cơ sở dữ liệu SQL Server  
> ✅ Sử dụng Pinecone cho tìm kiếm ngữ nghĩa  
> ✅ Sử dụng mô hình Gemini 2.0 Flash qua `langchain-google-genai`  
> ✅ Giao diện đơn giản với Streamlit

---

## 🔧 Công nghệ sử dụng

- 🧠 **LangChain** – xử lý logic chuỗi và truy xuất ngữ cảnh
- 🧬 **Pinecone** – vector DB lưu trữ mô tả sản phẩm
- 💬 **Google Gemini 2.0 Flash** – tạo phản hồi từ ngữ cảnh
- 🗃️ **SQL Server** – lưu trữ dữ liệu gốc (products, variants...)
- 🖥️ **Streamlit** – giao diện người dùng chatbot

---

## 📁 Cấu trúc thư mục

```
ChatBot/
├── .env
├── requirements.txt
├── README.md
├── data/
│   └── cleaned_products_catalog.csv
├── src/
│   ├── app.py                # Giao diện Streamlit
│   ├── pinecone_sync.py      # Đồng bộ dữ liệu từ SQL Server -> Pinecone
│   ├── data_ingestion.py     # Đưa dữ liệu vào SQL Server
```

---

## 🛠️ Cài đặt môi trường

### 1. Tạo Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # macOS / Linux
venv\Scripts\activate     # Windows
```

### 2. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

---

## 🔐 Tạo file `.env`

Tạo tệp `.env` trong thư mục gốc với nội dung:

```dotenv
GOOGLE_API_KEY=your_google_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
DB_SERVER=localhost
DB_DATABASE=ProductDB
DB_USERNAME=your_sql_username
DB_PASSWORD=your_sql_password
```

---

## 🗃️ Nhập dữ liệu vào SQL Server

Chạy script để nhập dữ liệu vào SQL Server:

```bash
python src/data_ingestion.py
```

---

## 🔄 Đồng bộ dữ liệu lên Pinecone

```bash
python src/pinecone_sync.py
```

---

## 🚀 Chạy chatbot

```bash
streamlit run src/app.py
```

---

## 🧠 Cách hoạt động

1. Người dùng đặt câu hỏi (ví dụ: *"Điện thoại màu black nào rẻ nhất?"*)
2. Câu hỏi được embedding và truy vấn trên **Pinecone**
3. Các mô tả liên quan được trả về và kết hợp với câu hỏi
4. **Gemini 2.0 Flash** tạo phản hồi dựa trên truy vấn + ngữ cảnh
5. Trả lại kết quả cho người dùng

---

## 📝 Ghi chú

- Đảm bảo bạn có quyền truy cập mô hình `gemini-2.0-flash` từ Google AI.
- Kiểm tra API key hợp lệ từ [Google AI Studio](https://makersuite.google.com/app).
- Mô hình `gemini-2.0-flash` không hỗ trợ những yêu cầu lớn > 8192 tokens.

---

## 📌 Tài liệu tham khảo

- [LangChain Docs](https://docs.langchain.com/)
- [Google AI Gemini API](https://ai.google.dev/)
- [Pinecone Docs](https://docs.pinecone.io/)
- [Streamlit Docs](https://docs.streamlit.io/)

---

Nếu bạn thấy dự án này hữu ích, hãy ⭐️ hoặc chia sẻ nhé!  
Mọi thắc mắc vui lòng liên hệ hoặc mở issue.
