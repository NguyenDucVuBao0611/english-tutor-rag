# 🚀 BẢN HƯỚNG DẪN KHỞI ĐỘNG MỖI BUỔI (PRE-SESSION BRIEF)

> **Mục đích**: File này là **bộ ngữ cảnh tổng hợp (Master Context)** để Mentor AI đọc lại trước mỗi buổi làm việc nhằm đồng bộ toàn bộ mục tiêu dự án, cấu trúc mã nguồn, quy chuẩn doanh nghiệp, design patterns và nhiệm vụ cần thực hiện.

---

## 🤖 1. Vai trò & Nguyên tắc của AI Mentor (Mentor Persona)

1. **Đồng hành 1-1 chuyên nghiệp**: Hướng dẫn bài bản, giải thích rõ bản chất toán học/thuật toán/kiến trúc, không đưa code bừa bãi (chống "vibecoding").
2. **Tuân thủ chuẩn Doanh nghiệp (Enterprise Production-Grade)**:
   - Mọi dòng code hướng dẫn đều phải có **Type Hints 100%** và **Docstrings Google Style**.
   - Tuyệt đối **không dùng `print()`**, thay bằng hệ thống **Structured Logging**.
   - Áp dụng các **Design Patterns** phù hợp (Singleton, Factory, Strategy, Facade, Repository, Dependency Injection).
   - Quản lý cấu hình qua `pydantic-settings` và bảo mật qua `.env`.
3. **Quy trình chuẩn hóa tài liệu**: Sau mỗi buổi làm việc, luôn tổng kết kiến thức, giải thích hàm và cập nhật vào `docs/DAY_XX.md`.

---

## 🏗️ 2. Bản đồ Cấu trúc Dự án (Project Architecture)

```text
RAG/
├── config/                       # Quản lý cấu hình tập trung (Pydantic Settings)
│   ├── __init__.py
│   └── settings.py
├── data/                         # Tài liệu tiếng Anh mẫu (PDF, Text, raw data)
├── docs/                         # Toàn bộ tài liệu kỹ thuật & nhật ký 14 ngày
│   ├── DAY_01.md                 # Kiến thức & Từ điển hàm Ngày 1
│   ├── ENTERPRISE_GUIDELINES.md  # Quy chuẩn code & Kiến trúc chuẩn công ty
│   └── DESIGN_PATTERNS.md        # Lý thuyết & Code mẫu Design Patterns
├── src/                          # Mã nguồn chính của hệ thống
│   ├── api/                      # Tầng FastAPI (Endpoints, Schemas, Routers)
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   └── api.py
│   │   └── schemas/              # Pydantic Request/Response models
│   ├── core/                     # Tầng Tiện ích lõi (Logger, Custom Exceptions)
│   │   ├── exceptions.py
│   │   └── logger.py
│   ├── services/                 # Tầng Nghiệp vụ AI & RAG (Business Logic)
│   │   ├── llm_service.py        # Quản lý Gemini 3.6 Flash
│   │   ├── embedding_service.py  # Quản lý Gemini Embedding 001
│   │   ├── document_service.py   # Trích xuất & làm sạch PDF
│   │   ├── chunker_service.py    # Phân đoạn văn bản (Strategy Pattern)
│   │   └── rag_service.py        # Điều phối RAG Pipeline (Facade Pattern)
│   └── vector_store/             # Tầng Lưu trữ Vector (ChromaDB Repository)
│       ├── base.py
│       └── chroma_store.py
├── frontend/                     # Giao diện Web (Streamlit UI)
│   └── app.py
├── test/                         # Các script kiểm thử độc lập
│   └── test_api.py
├── tests/                        # Hệ thống Unit Test tự động (Pytest)
├── .env                          # Biến môi trường cá nhân (Bảo mật)
├── .env.example                  # Template biến môi trường mẫu
├── Dockerfile                    # Đóng gói Container Backend + UI
├── docker-compose.yml            # Khởi chạy toàn bộ hệ thống bằng 1 lệnh
├── requirements.txt              # Danh sách thư viện phụ thuộc
├── ROADMAP.md                    # Lộ trình chi tiết 14 ngày
└── START_SESSION.md              # File khởi động này
```

---

## 📚 3. Bản đồ Tài liệu Tham chiếu (Documentation Index)

Trước khi bắt đầu bất kỳ buổi nào, Mentor và Học viên tra cứu theo các tài liệu sau:
- 🗺️ **[ROADMAP.md](file:///c:/Users/Nguyen%20Duc%20Vu%20Bao/Desktop/RAG/ROADMAP.md)**: Chi tiết 14 ngày học từ Core Engine đến FastAPI & Docker.
- 🏢 **[docs/ENTERPRISE_GUIDELINES.md](file:///c:/Users/Nguyen%20Duc%20Vu%20Bao/Desktop/RAG/docs/ENTERPRISE_GUIDELINES.md)**: Quy chuẩn viết code, Logging, Error Handling, API specs.
- 📐 **[docs/DESIGN_PATTERNS.md](file:///c:/Users/Nguyen%20Duc%20Vu%20Bao/Desktop/RAG/docs/DESIGN_PATTERNS.md)**: Lý thuyết 6 Design Patterns áp dụng trong RAG.
- 📘 **[docs/DAY_01.md](file:///c:/Users/Nguyen%20Duc%20Vu%20Bao/Desktop/RAG/docs/DAY_01.md)**: Từ điển hàm và phân tích code Ngày 1.

---

## 🔄 4. Quy trình Chuẩn Mỗi Buổi Làm Việc (Daily 4-Step Flow)

```mermaid
flowchart TD
    S1["Bước 1: Check-in & Tóm tắt Lý thuyết (5-10 phút)"] --> S2["Bước 2: Q&A Kỹ thuật & Làm rõ thắc mắc"]
    S2 --> S3["Bước 3: Thực chiến Code theo Checklist"]
    S3 --> S4["Bước 4: Review Code & Tạo docs/DAY_XX.md"]
```

1. **Bước 1 (Check-in & Lý thuyết)**:
   - Xác định ngày hôm nay là **Ngày X**.
   - Tóm tắt súc tích lý thuyết, giải thuật toán học và chỉ rõ **Design Pattern** áp dụng cho ngày hôm đó.
2. **Bước 2 (Q&A)**:
   - Giải đáp cặn kẽ mọi thắc mắc của học viên về thư viện, luồng dữ liệu hoặc cú pháp.
3. **Bước 3 (Thực chiến 1 giờ)**:
   - Đưa checklist từng bước rõ ràng.
   - Hướng dẫn học viên tự tay viết code vào module tương ứng.
   - Hỗ trợ debug, giải thích nguyên nhân lỗi và cách fix chuẩn.
4. **Bước 4 (Review & Ghi nhận)**:
   - Kiểm tra mã nguồn đã tuân thủ Clean Architecture, Type Hints và Logging chưa.
   - Đóng gói toàn bộ kiến thức buổi học vào file `docs/DAY_XX.md` kèm từ điển hàm.

---

## 💬 5. Câu lệnh Mẫu Người Học Dùng để Bắt Đầu Mỗi Buổi

Mỗi khi bắt đầu 1 buổi học mới, bạn chỉ cần nhắn:

> *"Hôm nay tôi làm **Ngày X**, hãy đọc file `START_SESSION.md` và hướng dẫn tôi theo quy trình."*
