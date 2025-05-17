from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

llm = ChatGroq(model_name="llama3-70b-8192", temperature=0.0)

system_message = SystemMessage(
    content=(
        "Bạn là trợ lý bán hàng. Người dùng sẽ hỏi về sản phẩm và bạn sẽ cung cấp thông tin về sản phẩm dựa trên danh sách sản phẩm đã cho. "
        "Hãy đọc danh sách sản phẩm bên dưới và tìm những sản phẩm phù hợp với tiêu chí của họ. "
        "❗ Tất cả câu trả lời phải bằng TIẾNG VIỆT, bao gồm các giá trị như màu sắc, trạng thái, thuộc tính kỹ thuật. "
        "Tự động dịch các giá trị từ tiếng Anh sang tiếng Việt một cách chính xác theo ngữ cảnh. "
        "Chỉ sử dụng thông tin trong danh sách sản phẩm, không bịa đặt, không suy đoán thêm."
    )
)

def shopbot_ai(user_query: str, context: str) -> str:
    full_prompt = (
        f"Câu hỏi của người dùng: {user_query}  \n  \n"
        f"Danh sách sản phẩm:  \n{context}  \n  \n"

        f"🔁 Lưu ý QUAN TRỌNG:  \n"
        f"- Nếu có nhiều sản phẩm cùng tên, CHỈ chọn 1 bản đại diện (loại bỏ bản khác).  \n"
        f"- **Bạn PHẢI lọc sản phẩm DỰA TRÊN TIÊU CHÍ người dùng đưa ra.**  \n"
        f"- **Không được liệt kê sản phẩm nào KHÔNG PHÙ HỢP với yêu cầu.**  \n"
        f"- **Đặc biệt, nếu người dùng hỏi về khoảng giá, màu sắc, cấu hình,... thì chỉ chọn sản phẩm thỏa mãn tất cả tiêu chí.**  \n"

        f"❗ Vui lòng TRẢ LỜI BẰNG TIẾNG VIỆT, GIỮ ĐÚNG FORMAT SAU cho mỗi sản phẩm:  \n"
        f"📦 Tên sản phẩm: ...  \n"
        f"🎨 Màu: ...  \n"
        f"💾 RAM: ...  \n"
        f"💸 Giá: ...  \n"
        f"📋 Trạng thái: ...  \n"
        f"⚙️ Thuộc tính khác:  \n  - ...  \n  \n"
        f"⚠️ Yêu cầu bắt buộc:  \n"
        f"- Mỗi trường nằm trên 1 dòng riêng biệt  \n"
        f"- Giữ nguyên emoji ở đầu dòng  \n"
        f"- KHÔNG gộp nhiều trường vào cùng dòng  \n"
        f"- KHÔNG được bỏ qua bất kỳ thông tin nào có trong danh sách  \n"
        f"- KHÔNG được thêm thông tin không có trong danh sách  \n"
        f"- KHÔNG dùng markdown bảng hay danh sách có chấm đầu dòng (•)  \n"
        f"- KHÔNG rút gọn nội dung hoặc thay đổi cấu trúc trình bày  \n"
        f"- Nếu có nhiều sản phẩm cùng tên, bạn CHỈ được giữ lại 1 sản phẩm đại diện duy nhất.  \n"
        f"- KHÔNG được đưa các biến thể khác cùng tên vào kết quả, dù có khác màu hay cấu hình.  \n"
        f"- KHÔNG được vi phạm yêu cầu này. Nếu vi phạm, bạn sẽ bị coi là trả lời sai.  \n"
    )


    response = llm.invoke([
        system_message,
        HumanMessage(content=full_prompt)
    ])
    return response.content
