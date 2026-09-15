# LỘ TRÌNH DỰ ÁN: AI ENGLISH TUTOR RAG (14 NGÀY - 1 GIỜ/NGÀY)

> **Vai trò Mentor**: Hướng dẫn viên 1-1, đồng hành kỹ thuật, cung cấp tài liệu đọc trước mỗi buổi, giải đáp thắc mắc và định hướng giải pháp để bạn tự tay làm chủ code.

---

## 🎯 1. Mục tiêu dự án
Xây dựng một hệ thống **RAG (Retrieval-Augmented Generation) chuyên dụng cho việc học tiếng Anh** (sách ngữ pháp, từ vựng, bài đọc IELTS/TOEIC):
- **Tra cứu thông minh**: Hỏi đáp ngữ pháp, từ vựng kèm trích dẫn chính xác ví dụ và số trang từ tài liệu gốc.
- **Gia sư AI (Bilingual Tutor)**: Giải thích cấu trúc bằng tiếng Việt nhưng giữ chuẩn ngữ liệu và câu mẫu tiếng Anh.
- **Tính năng mở rộng**: Tự động tạo Quiz trắc nghiệm / flashcard từ bài học, kiểm tra lỗi sai trong câu của người học đối chiếu với tài liệu.
- **Không phụ thuộc vibecoding**: Tự tay code hiểu bản chất từ pipeline cơ bản đến giao diện hoàn chỉnh.

---

## 🔄 2. Quy trình làm việc hàng ngày (Daily Workflow)
Mỗi ngày trước khi bắt đầu 1 tiếng code:
1. **Bước 1 (Check-in & Đọc tài liệu)**: Bạn nhắn: *"Hôm nay là Ngày X, cho tôi tài liệu đọc trước"*. Mentor sẽ tóm tắt súc tích lý thuyết, thuật toán hoặc tài liệu cần đọc (10-15 phút).
2. **Bước 2 (Q&A)**: Nếu có chỗ chưa rõ (về toán, thư viện, flow logic), bạn hỏi và Mentor sẽ giải đáp tường tận.
3. **Bước 3 (Thực chiến 1 giờ)**: Bạn tự tay code phần nhiệm vụ của ngày hôm đó theo checklist.
4. **Bước 4 (Review & Ghi nhận)**: Đánh dấu hoàn thành milestone trong ngày.

---

## 📅 3. Chi tiết lộ trình 14 ngày

### 🔰 TUẦN 1: XÂY DỰNG CORE ENGINE & HIỂU SÂU BẢN CHẤT

#### **Ngày 1: Thiết lập môi trường & Hello World LLM/Embedding API**
- **Tài liệu đọc trước**: Cấu trúc project Python chuẩn, cách hoạt động của LLM API & Text Embedding API, quản lý biến môi trường (`.env`).
- **Nhiệm vụ 1 giờ**:
  - Tạo virtual environment (`venv`), cài `python-dotenv`, SDK (`google-genai` hoặc `openai`).
  - Viết file test gọi LLM với prompt định hình vai trò gia sư tiếng Anh.
  - Viết hàm lấy vector embedding của 1 câu tiếng Anh mẫu và kiểm tra số chiều vector.
- **Output**: File `test_api.py` chạy thành công trên terminal.

---

#### **Ngày 2: Trích xuất Text & Làm sạch tài liệu học tiếng Anh**
- **Tài liệu đọc trước**: Cấu trúc file PDF văn bản, thư viện `pypdf`/`pdfplumber`, các kỹ thuật text cleaning đặc thù cho sách học tiếng Anh (xử lý bullet points, bảng biểu cơ bản, loại bỏ header/footer).
- **Nhiệm vụ 1 giờ**:
  - Chuẩn bị 1-2 tài liệu tiếng Anh mẫu (PDF chương sách ngữ pháp hoặc bài đọc).
  - Viết module `loader.py` đọc từng trang, lưu lại metadata (tên sách, số trang).
  - Làm sạch văn bản (loại bỏ ngắt dòng vô nghĩa, chuẩn hóa khoảng trắng).
- **Output**: Script trích xuất văn bản sạch từ PDF kèm thông tin số trang.

---

#### **Ngày 3: Kỹ thuật Chunking thông minh theo cấu trúc bài học**
- **Tài liệu đọc trước**: Tại sao Fixed-size chunking làm hỏng ngữ cảnh học tiếng Anh? Khái niệm `RecursiveCharacterTextSplitter`, `chunk_size` và `chunk_overlap`.
- **Nhiệm vụ 1 giờ**:
  - Tự viết hàm cắt đoạn hoặc cấu hình splitter ưu tiên ngắt theo đoạn văn (`\n\n`), tiêu đề bài/Unit, hoặc câu hoàn chỉnh (`. `).
  - Đảm bảo mỗi chunk giữ trọn vẹn: `Quy tắc ngữ pháp + Ví dụ`.
  - In ra 5 chunks mẫu để kiểm tra độ trọn vẹn ngữ nghĩa.
- **Output**: Module `chunker.py` chia văn bản thành các chunks chất lượng cao.

---

#### **Ngày 4: Bản chất Vector Search & Ôn lại Toán AI**
- **Tài liệu đọc trước**: Không gian vector ngữ nghĩa (Semantic Vector Space), công thức Cosine Similarity, Dot Product, lý do cosine similarity hiệu quả với embedding đã normalize.
- **Nhiệm vụ 1 giờ**:
  - Tạo embeddings cho toàn bộ chunks của Ngày 3.
  - Tự dùng **NumPy** viết hàm `cosine_similarity(query_vector, chunk_vectors)`.
  - Đưa vào 1 câu hỏi tiếng Anh/tiếng Việt và in ra Top-3 chunks có độ tương đồng cao nhất.
- **Output**: Module `similarity_test.py` tìm đúng đoạn tài liệu bằng code NumPy thuần.

---

#### **Ngày 5: Tích hợp Vector Database chuyên dụng (ChromaDB)**
- **Tài liệu đọc trước**: Vector Database là gì? Cấu trúc Collections, Persistent Storage vs In-Memory, Metadata Filtering trong ChromaDB.
- **Nhiệm vụ 1 giờ**:
  - Cài đặt và khởi tạo ChromaDB local lưu dạng sqlite/file.
  - Viết hàm Ingest: Đọc PDF $\rightarrow$ Chunk $\rightarrow$ Add vào ChromaDB kèm metadata (`book`, `unit`, `page`).
  - Viết hàm Query truy vấn Top-k chunks từ ChromaDB.
- **Output**: Module `vector_store.py` lưu trữ và truy vấn tài liệu ổn định.

---

#### **Ngày 6: Xây dựng RAG Generation & Grounded Prompting**
- **Tài liệu đọc trước**: RAG Prompting Anatomy (System Prompt, Context Injection, User Query), kỹ thuật Grounding chống ảo giác (Hallucination), cấu trúc phản hồi của Gia sư tiếng Anh.
- **Nhiệm vụ 1 giờ**:
  - Thiết kế System Prompt chuẩn gia sư: Giải thích dễ hiểu, luôn đưa ra ví dụ lấy đúng từ context, nếu không có trong tài liệu thì thông báo không biết.
  - Nối luồng hoàn chỉnh: `Câu hỏi` $\rightarrow$ `ChromaDB Retrieve` $\rightarrow$ `Format Context` $\rightarrow$ `LLM Generation`.
- **Output**: Script `rag_engine.py` nhận câu hỏi qua terminal và in câu trả lời có căn cứ.

---

#### **Ngày 7: Source Citations & Hoàn thành Milestone 1**
- **Tài liệu đọc trước**: Kỹ thuật trích dẫn nguồn (Source Citation) và kiểm tra tính trung thực của câu trả lời.
- **Nhiệm vụ 1 giờ**:
  - Tinh chỉnh output để luôn hiển thị rõ: `[Nguồn: Sách X, Trang Y]`.
  - Viết vòng lặp CLI tương tác trực tiếp trên Terminal để hỏi đáp liên tục.
  - Test 5 ca hỏi đáp thực tế (ngữ pháp, từ vựng, collocation).
- **🎯 Milestone 1**: Hệ thống CLI RAG chuyên tra cứu tài liệu tiếng Anh chạy độc lập, tự viết code.

---

### 🚀 TUẦN 2: DỰNG GIAO DIỆN, NÂNG CAO TÍNH NĂNG & ĐÓNG GÓI

#### **Ngày 8: Dựng Web UI trực quan với Streamlit**
- **Tài liệu đọc trước**: Kiến trúc Streamlit (Session State, Re-run model), các component chat: `st.chat_message`, `st.chat_input`, `st.sidebar`.
- **Nhiệm vụ 1 giờ**:
  - Dựng giao diện Web: Sidebar upload PDF và chọn sách; Khung chính hiển thị lịch sử chat.
  - Kết nối giao diện với `rag_engine.py` từ Tuần 1.
- **Output**: Ứng dụng web chạy local tại `localhost:8501`.

---

#### **Ngày 9: Ghi nhớ ngữ cảnh hội thoại (Conversational Memory)**
- **Tài liệu đọc trước**: Thách thức của câu hỏi nối tiếp trong RAG (Ví dụ: *"Give me 3 more examples of that rule"*), kỹ thuật Condense Question (viết lại câu hỏi độc lập).
- **Nhiệm vụ 1 giờ**:
  - Viết hàm tiền xử lý: Dùng LLM viết lại câu hỏi nối tiếp dựa trên lịch sử chat trước khi đưa vào ChromaDB.
  - Cập nhật chat memory trong Streamlit `st.session_state`.
- **Output**: Chatbot trả lời thông minh các câu hỏi nối tiếp mà không mất dấu chủ đề.

---

#### **Ngày 10: Tính năng "Tạo Quiz / Flashcard tự động" từ bài học**
- **Tài liệu đọc trước**: Structured Outputs (JSON Mode / Pydantic schema) trong LLM để tạo câu hỏi trắc nghiệm chuẩn xác.
- **Nhiệm vụ 1 giờ**:
  - Viết prompt chuyên dụng nhận context bài học và sinh ra 3 câu trắc nghiệm (câu hỏi, 4 đáp án A/B/C/D, đáp án đúng, giải thích).
  - Hiển thị Quiz tương tác trên giao diện Streamlit (cho người dùng bấm chọn đáp án).
- **Output**: Chế độ "Luyện tập trắc nghiệm" hoạt động trực tiếp từ tài liệu đã học.

---

#### **Ngày 11: Tính năng "Check My English" đối chiếu tài liệu**
- **Tài liệu đọc trước**: Error Analysis Prompting, cách truy xuất các quy tắc ngữ pháp tương ứng với lỗi người học mắc phải.
- **Nhiệm vụ 1 giờ**:
  - Tạo chức năng: Người học nhập 1 câu tiếng Anh của họ $\rightarrow$ Hệ thống tra cứu quy tắc trong tài liệu $\rightarrow$ Báo lỗi sai (nếu có) và trích dẫn quy tắc trong sách để sửa.
- **Output**: Tính năng sửa câu và tra cứu quy tắc tương ứng.

---

#### **Ngày 12: Tối ưu hóa Retrieval & Giảm thiểu Hallucination**
- **Tài liệu đọc trước**: Khái niệm Hybrid Search (kết hợp Keyword BM25 + Semantic Vector), Reranking cơ bản, kỹ thuật Negative Prompting.
- **Nhiệm vụ 1 giờ**:
  - Tinh chỉnh ngưỡng khoảng cách similarity (distance threshold) để lọc bỏ các đoạn rác không liên quan.
  - Cải tiến câu trả lời fallback khi câu hỏi nằm ngoài phạm vi tài liệu.
- **Output**: Hệ thống chặt chẽ, không bịa đặt kiến thức ngoài tài liệu.

---

#### **Ngày 13: Đánh giá chất lượng RAG (RAG Triad Evaluation)**
- **Tài liệu đọc trước**: Bộ 3 tiêu chí đánh giá RAG (Context Relevance, Groundedness, Answer Relevance).
- **Nhiệm vụ 1 giờ**:
  - Chuẩn bị bộ test 10 câu hỏi chuẩn với tài liệu thật.
  - Tự đánh giá điểm số của hệ thống theo 3 tiêu chí trên, ghi nhận các trường hợp trả lời chưa chuẩn và tinh chỉnh prompt/chunking.
- **Output**: Bảng đánh giá chất lượng hệ thống (`evaluation_report.md`).

---

#### **Ngày 14: Tái cấu trúc (Refactor), Viết README & Hoàn thiện Portfolio**
- **Tài liệu đọc trước**: Cách viết một README chuẩn kỹ thuật cho dự án AI/RAG, quy chuẩn đóng gói mã nguồn (`requirements.txt`, modular design).
- **Nhiệm vụ 1 giờ**:
  - Dọn dẹp mã nguồn, tách module gọn gàng:
    ```text
    RAG/
    ├── data/               # Tài liệu học tiếng Anh mẫu
    ├── src/
    │   ├── loader.py
    │   ├── chunker.py
    │   ├── vector_store.py
    │   └── tutor_engine.py
    ├── app.py              # Streamlit Web App
    ├── requirements.txt
    └── README.md
    ```
  - Viết `README.md` chuyên nghiệp (kiến trúc luồng, ảnh chụp giao diện, hướng dẫn cài đặt).
- **🎯 Milestone 2**: Dự án hoàn chỉnh 100%, sẵn sàng đưa lên GitHub/CV.
