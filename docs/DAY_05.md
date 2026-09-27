# 📘 NGÀY 5: VECTOR STORE REPOSITORY (TÍCH HỢP CHROMADB)

> **Dự án**: AI English Tutor RAG (14 Ngày)  
> **Trọng tâm Ngày 5**: Xây dựng tầng lưu trữ Vector Database bền vững sử dụng **ChromaDB** theo mẫu thiết kế **Repository Pattern** chuẩn Enterprise; tìm hiểu kiến trúc lưu trữ lai (Hybrid Storage: SQLite + HNSW Binary Files); tối ưu hóa tìm kiếm Top-k kết hợp bộ lọc Metadata đa tầng; kiểm chứng tính bền vững (Persistence) và bảo toàn dữ liệu khi khởi động lại ứng dụng.

---

## 📑 MỤC LỤC
1. [Tại sao cần Vector Database chuyên dụng thay vì NumPy?](#1-tại-sao-cần-vector-database-chuyên-dụng-thay-vì-numpy)
2. [Cơ chế Lưu trữ Ổ cứng của ChromaDB (Hybrid Storage Architecture)](#2-cơ-chế-lưu-trữ-ổ-cứng-của-chromadb-hybrid-storage-architecture)
3. [Thiết kế Kiến trúc: Repository Pattern](#3-thiết-kế-kiến-trúc-repository-pattern)
4. [Giải phẫu Chi tiết Mã Nguồn Vector Store](#4-giải-phẫu-chi-tiết-mã-nguồn-vector-store)
   - [4.1. Hợp đồng trừu tượng: `BaseVectorStore`](#41-hợp-đồng-trừu-tượng-basevectorstore)
   - [4.2. Thực thi cụ thể: `ChromaVectorStore`](#42-thực-thi-cụ-thể-chromavectorstore)
5. [Từ điển các Hàm & Công cụ có sẵn của Thư viện ChromaDB](#5-từ-điển-các-hàm--công-cụ-có-sẵn-của-thư-viện-chromadb)
6. [Kết quả Kiểm thử Thực tế & Cầu nối sang Ngày 6](#6-kết-quả-kiểm-thử-thực-tế--cầu-nối-sang-ngày-6)

---

## 🎯 1. Tại sao cần Vector Database chuyên dụng thay vì NumPy?

Ở Ngày 4, chúng ta đã tự tay viết thuật toán **Cosine Similarity** bằng NumPy và xếp hạng kết quả chính xác 100%. Tuy nhiên, cách tiếp cận đó chỉ phù hợp để nghiên cứu bản chất toán học vì gặp phải **3 rào cản lớn trong Production**:

```mermaid
flowchart TD
    NumPy["Cách làm Ngày 4 (NumPy thuần)"] --> P1["❌ 1. Mất dữ liệu khi dừng tiến trình\nVector chỉ nằm trong RAM, tắt server là mất sạch, phải tạo lại từ đầu tốn tiền API."]
    NumPy --> P2["❌ 2. Chậm khi dữ liệu mở rộng (Vét cạn Brute-force O(N))\nNếu sách có 100.000 chunks, mỗi truy vấn phải nhân ma trận với cả 100.000 dòng."]
    NumPy --> P3["❌ 3. Không hỗ trợ Lọc Metadata phức tạp\nRất khó khăn khi cần: 'Chỉ tìm trong Unit 7 của sách English Grammar in Use'."]
```

👉 **ChromaDB** sinh ra để giải quyết triệt để 3 rào cản trên bằng cách:
1. **Lưu trữ bền vững (Persistence)** xuống đĩa cứng (chỉ embed sách 1 lần duy nhất).
2. **Tăng tốc tìm kiếm qua cấu trúc Đồ thị HNSW** (Approximate Nearest Neighbors - ANN) với độ phức tạp $O(\log N)$.
3. **Quản lý dữ liệu đi kèm (Metadata Filtering)** hỗ trợ toán tử SQL linh hoạt (`$eq`, `$in`, `$gt`...).

---

## 💾 2. Cơ chế Lưu trữ Ổ cứng của ChromaDB (Hybrid Storage Architecture)

### 2.1. Tham số `persist_directory (Optional[Path | str])` là gì?
- **"Persistence" (Lưu trữ bền vững)**: Đối lập với **In-Memory (Bộ nhớ RAM tạm thời)**:
  - *Nếu không có persistence*: Tắt chương trình Python hoặc restart server là toàn bộ vector bốc hơi 100%. Lần sau bật lên lại mất 10 phút và tốn tiền gọi API Gemini để nhúng lại từ đầu.
  - *Khi có `persist_directory`*: Dữ liệu ghi thẳng xuống ổ đĩa máy tính (SSD/HDD). Khởi động lại ứng dụng chỉ mất **0.1 giây**, dữ liệu nạp lên dùng ngay, không tốn thêm 1 xu tiền API.
- **Type Hint `Optional[Path | str]`**: Quy chuẩn Clean Code cho phép người dùng truyền vào chuỗi string thông thường (`"chroma_data"`) hoặc đối tượng `Path("chroma_data")` của thư viện `pathlib`. Nếu để trống (`None`), hệ thống tự động lấy đường dẫn mặc định trong `src.config.CHROMA_DIR`.

---

### 2.2. Cấu trúc lưu trữ thư mục thực tế
Khi cấu hình `chromadb.PersistentClient(path="./chroma_data")`, ChromaDB không lưu thành file JSON hay văn bản thô, mà sử dụng **Kiến trúc Lai (Hybrid Storage)** kết hợp giữa 2 công nghệ:

```text
chroma_data/
├── chroma.sqlite3                  <--- 1. CSDL SQLite (Thủ thư ghi sổ: Text, ID, Metadata & ACID)
└── <collection-uuid>/              <--- 2. Thư mục File Nhị phân HNSW (Vận động viên định vị: Vector & Graph)
    ├── data_level0.bin             <--- Mạng lưới liên kết vector dạng byte thô
    ├── header.bin                  <--- Cấu hình số chiều (3072) và độ dài index
    └── length.bin
```

---

### 2.3. SQLite vs HNSW: Sự Phân Chia Vai Trò Tuyệt Hảo

| Tiêu chí | 🗄️ SQLite Database (`chroma.sqlite3`) | ⚡ HNSW Index (`.bin` files) |
| :--- | :--- | :--- |
| **Hình tượng** | **Người thủ thư ghi sổ cẩn thận** | **Vận động viên định vị siêu tốc** |
| **Bản chất** | Hệ quản trị cơ sở dữ liệu quan hệ nhúng (RDBMS). | Thuật toán cấu trúc dữ liệu đồ thị thế giới nhỏ đa tầng (Hierarchical Navigable Small World). |
| **Dữ liệu quản lý** | - Nội dung văn bản gốc (`document`).<br>- Mã định danh (`ids`).<br>- Thuộc tính nguồn gốc (`metadata`: book, page, unit). | - Tọa độ số học của các vector 3072 chiều.<br>- Các đường nối đồ thị láng giềng giữa các vector. |
| **Sức mạnh lõi** | - Đảm bảo tính toàn vẹn dữ liệu **ACID & WAL log**.<br>- Xử lý các phép lọc điều kiện logic (`where={"book": "Grammar"}`). | - Tốc độ tìm kiếm vector tiệm cận tức thì: **$O(\log N)$** thay vì vét cạn $O(N)$ như NumPy.<br>- Nhảy qua các tầng đồ thị (như các chuyến bay chuyển tiếp) để tới gần mục tiêu chỉ trong 1-2 mili-giây. |
| **Điểm yếu** | **Không biết tính toán vector similarity**. Bắt SQLite nhân ma trận 100.000 vector sẽ làm đơ máy. | **Mù chữ**. HNSW chỉ biết con số và ID (`0, 1, 2...`), hoàn toàn không biết đoạn văn viết chữ gì hay thuộc trang mấy. |

---

### 2.4. Màn Phối Hợp Khi Bạn Thực Hiện Một Truy Vấn

Khi bạn gọi lệnh tìm kiếm:
```python
store.similarity_search("How to use present perfect?", top_k=2, where={"book": "Grammar in Use"})
```

ChromaDB kích hoạt quy trình phối hợp nhịp nhàng giữa HNSW và SQLite:

```mermaid
sequenceDiagram
    participant User as Ứng dụng (RAG Service)
    participant HNSW as ⚡ HNSW Index (.bin)
    participant SQLite as 🗄️ SQLite Database (.sqlite3)

    User->>HNSW: 1. Đưa vector câu hỏi vào: "Tìm các vector ngữ nghĩa gần nhất?"
    HNSW-->>HNSW: Nhảy theo phân cấp đồ thị đa tầng (mất ~1-2ms)
    HNSW->>SQLite: 2. HNSW báo: "Tìm thấy Top ID gần nhất là ['chunk_1', 'chunk_5']!"
    SQLite-->>SQLite: 3. Lọc kiểm tra: "chunk_1 có thuộc sách 'Grammar in Use' không?" -> ĐẠT!
    SQLite->>User: 4. Rút trong kho ra đoạn văn bản gốc + số trang trả về kết quả!
```

👉 **Kết luận**: HNSW đem lại **TỐC ĐỘ ÁNH SÁNG** trong không gian vector đa chiều, còn SQLite đem lại **SỰ AN TOÀN VÀ CHÍNH XÁC** cho dữ liệu văn bản. Thiếu một trong hai thì không thể có một Vector Database chuẩn Production.

---

## 🏛️ 3. Thiết kế Kiến trúc: Repository Pattern

```mermaid
flowchart TD
    subgraph Business ["Tầng Nghiệp vụ (Business Layer)"]
        TutorRAG["RAGService / EnglishTutorFacade"]
    end

    subgraph Interface ["Tầng Trừu tượng (Contract Layer)"]
        BaseRepo["<<Interface>> BaseVectorStore\n(+add_documents, +similarity_search, +count)"]
    end

    subgraph Concrete ["Tầng Thực thi (Concrete Repository)"]
        ChromaStore["ChromaVectorStore\n(Sử dụng ChromaDB - Hiện tại)"]
        QdrantStore["QdrantVectorStore\n(Mở rộng tương lai)"]
        PineconeStore["PineconeVectorStore\n(Mở rộng Cloud tương lai)"]
    end

    subgraph Storage ["Tầng Đĩa cứng (Disk Persistence)"]
        DiskStore[("chroma_data/ (SQLite3 + HNSW Binary)")]
    end

    TutorRAG --> BaseRepo
    BaseRepo <|-- ChromaStore
    BaseRepo <|-.-> QdrantStore
    BaseRepo <|-.-> PineconeStore
    ChromaStore --> DiskStore
```

### Lợi ích chuẩn Enterprise:
1. **Loose Coupling (Giảm sự phụ thuộc)**: Tầng nghiệp vụ không import trực tiếp `chromadb`. Nếu sau này công ty yêu cầu chuyển sang Qdrant hoặc Pinecone, chỉ cần viết một class mới kế thừa `BaseVectorStore` mà không phải sửa một dòng code nào trong `RAGService`.
2. **Testability (Dễ kiểm thử)**: Khi viết Unit Test cho tầng Business, ta có thể inject một Mock Vector Store mà không cần phải chạy cơ sở dữ liệu thật.

---

## 🔍 4. Giải phẫu Chi tiết Mã Nguồn Vector Store

### 4.1. Hợp đồng trừu tượng: [`src/vector_store/base.py`](file:///c:/Users/Nguyen%20Duc%20Vu%20Bao/Desktop/RAG/src/vector_store/base.py)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseVectorStore(ABC):
    @abstractmethod
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Lưu trữ danh sách các đoạn văn bản (chunks) và metadata."""
        pass

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        top_k: int = 3,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Tìm kiếm Top-k đoạn văn bản có độ tương đồng ngữ nghĩa cao nhất."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Đếm tổng số lượng bản ghi trong kho."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Xóa sạch bộ sưu tập."""
        pass
```

---

### 4.2. Thực thi cụ thể: [`src/vector_store/chroma_store.py`](file:///c:/Users/Nguyen%20Duc%20Vu%20Bao/Desktop/RAG/src/vector_store/chroma_store.py)

#### Điểm sáng kỹ thuật:
1. **Dependency Injection & Singleton**:
   ```python
   self.embedding_service = embedding_service or EmbeddingService()
   ```
   Tự động tái sử dụng `EmbeddingService` Singleton đã viết ở Ngày 4, duy trì 1 client kết nối duy nhất tới Gemini API.
2. **Không gian Khoảng cách Cosine (`hnsw:space = cosine`)**:
   ```python
   self.collection = self.client.get_or_create_collection(
       name=self.collection_name,
       metadata={"hnsw:space": "cosine"},
   )
   ```
   Mặc định ChromaDB dùng $L2$ squared. Thiết lập `"hnsw:space": "cosine"` giúp chuẩn hóa việc so khớp góc lệch ngữ nghĩa.
3. **Quy đổi Khoảng cách sang Điểm tương đồng**:
   ```python
   # Trong không gian Cosine: Cosine Distance = 1 - Cosine Similarity
   score = max(0.0, 1.0 - dist)
   ```
   Chuyển đổi `distance` của ChromaDB thành `score` trực quan (trong khoảng $[0.0, 1.0]$, điểm càng cao càng liên quan).

### 4.3. Góc Code Review & Bắt Lỗi: Những Câu Hỏi Đào Sâu Cốt Lõi

Dưới đây là bản tổng hợp các câu hỏi phản biện kỹ thuật và bài học kiến trúc xuất sắc đã được mổ xẻ trong buổi học:

#### 1. `src.config.CHROMA_DIR` là gì? Cơ chế "Truyền tham số" hoạt động ra sao?
* **"Tham số" (Parameter)**: Là các biến nằm trong ngoặc tròn `def __init__(self, collection_name, persist_directory)`.
* **"Truyền tham số" (Passing argument)**: Là hành động đưa giá trị cụ thể vào khi gọi `ChromaVectorStore(persist_directory=...)`.
* **Cơ chế fallback với toán tử `or`**:
  ```python
  self.persist_directory = Path(persist_directory or CHROMA_DIR)
  ```
  - *Nếu không truyền gì (`None`)*: Toán tử `or` tự động lấy hằng số mặc định `CHROMA_DIR` (`RAG/chroma_data/`) định nghĩa trong `src/config.py`.
  - *Nếu tự đưa input theo ý mình*: Hệ thống sẽ lấy đúng đường dẫn bạn truyền vào (ví dụ thư mục test tạm thời `test_chroma_db/`).
* **Nguyên tắc Single Source of Truth**: Không bao giờ "hardcode" chuỗi `"chroma_data"` rải rác ở khắp các file. Khi cần đổi ổ đĩa, chỉ cần sửa 1 dòng trong `src/config.py` là toàn hệ thống tự động ăn theo.

---

#### 2. Hàm `add_documents` nạp từng đoạn hay nạp cả lô (Batch)?
* **Bản chất**: Hàm nạp **NGUYÊN CẢ LÔ (Batch) nhiều đoạn cùng một lúc**, thể hiện qua type hint `documents: List[str]`.
* **Tại sao không nạp từng đoạn một?**:
  - Nếu có 1.000 chunks mà nạp từng đoạn: Bạn phải gửi 1.000 request qua mạng tới Google API và mở/đóng file SQLite 1.000 lần $\rightarrow$ Mất hàng chục phút và dễ bị Google khóa API vì spam connection.
  - Nạp cả lô (Batch): Gom 1.000 chunks gửi 1 lần $\rightarrow$ SQLite mở 1 giao dịch duy nhất, nạp xong toàn bộ chỉ trong vài giây!
* **Nếu chỉ muốn nạp 1 đoạn duy nhất**: Đơn giản chỉ cần bọc đoạn đó trong dấu ngoặc vuông `store.add_documents(documents=["Đoạn duy nhất"])`.

---

#### 3. Trong ChromaDB đã có sẵn thuật toán so sánh Cosine chưa?
* **Có sẵn 100%**: ChromaDB tích hợp sẵn các thuật toán tính khoảng cách vector viết bằng C++/Rust tối ưu hóa phần cứng SIMD.
* **Kích hoạt ở dòng 53**: `metadata={"hnsw:space": "cosine"}` ra lệnh cho ChromaDB dùng khoảng cách Cosine.
* **3 thước đo phổ biến**:
  - `"cosine"`: Đo góc lệch, chuẩn số 1 cho văn bản/NLP (không phụ thuộc độ dài câu).
  - `"l2"`: Khoảng cách đường thẳng Euclid, hay dùng cho Computer Vision.
  - `"ip"`: Inner Product (Tích vô hướng).
* **Quy đổi Distance sang Score**: ChromaDB trả về `distance` (càng gần 0 càng giống). Code dùng công thức `score = max(0.0, 1.0 - distance)` để chuyển thành thang điểm tương đồng $[0.0, 1.0]$ trực quan cho người dùng.

---

#### 4. Ý nghĩa của tham số $k$ trong `top_k: int = 3`
* Trong khoa học dữ liệu và AI, chữ **$k$** là quy ước toán học kinh điển cho thuật toán **k-Nearest Neighbors (kNN)** và bài toán **Top-k Ranking**.
* Nó đại diện cho **số lượng kết quả gần nhất** cần lấy ra. Mặc định $k = 3$, nhưng người dùng có thể tùy biến `top_k=1` (lấy 1 đoạn hay nhất) hoặc `top_k=5` (lấy 5 đoạn).

---

#### 5. Tại sao bắt buộc phải có hàm xóa `reset()`?
Hàm `reset()` phục vụ 3 lý do sống còn:
1. **Kiểm thử tự động (Test Isolation)**: Nếu không xóa trước khi test, mỗi lần chạy script test dữ liệu sẽ bị cộng dồn (5 bản ghi $\rightarrow$ 10 $\rightarrow$ 15), khiến lệnh kiểm tra `assert count == 5` bị FAIL ngay lập tức!
2. **Tái nạp dữ liệu (Re-indexing)**: Khi sách có bản in mới hoặc khi ta đổi cách cắt chunk, cần xóa bộ sưu tập cũ để nạp lại từ đầu, tránh tình trạng sách cũ và sách mới bị đè chồng chéo lên nhau.
3. **Chuẩn CRUD kinh điển**: Một hệ thống lưu trữ bắt buộc phải có đủ 4 thao tác: Create (`add_documents`), Read (`similarity_search`), Update, và Delete (`reset`).

---

## 📖 5. Từ điển các Hàm & Công cụ có sẵn của Thư viện ChromaDB

| Hàm / Thuộc tính | Cú pháp sử dụng | Công dụng & Bản chất kỹ thuật |
| :--- | :--- | :--- |
| **`chromadb.PersistentClient`** | `client = chromadb.PersistentClient(path="./data")` | Khởi tạo kết nối lưu trữ bền vững xuống thư mục cục bộ (tự động tạo SQLite và cấu trúc file index). |
| **`get_or_create_collection`** | `client.get_or_create_collection(name, metadata=...)` | Lấy collection nếu đã có, hoặc tạo mới nếu chưa tồn tại (tương tự `CREATE TABLE IF NOT EXISTS`). |
| **`collection.add`** | `collection.add(ids=..., embeddings=..., documents=..., metadatas=...)` | Nạp đồng thời cả 4 thành phần: mã định danh, vector nhúng, văn bản gốc và thẻ thông tin metadata. |
| **`collection.query`** | `collection.query(query_embeddings=..., n_results=3, where=...)` | Thực hiện tìm kiếm vector láng giềng gần nhất (ANN qua HNSW) kết hợp bộ lọc metadata (`where`). |
| **`collection.count`** | `collection.count()` | Trả về tổng số lượng bản ghi (vector) hiện có trong collection. |
| **`client.delete_collection`** | `client.delete_collection(name=...)` | Xóa sổ hoàn toàn một collection và giải phóng tài nguyên đĩa cứng. |
| **`uuid.uuid4().hex`** | `f"chunk_{uuid.uuid4().hex[:10]}"` | Sinh chuỗi mã định danh ngẫu nhiên chuẩn 128-bit không trùng lặp cho từng chunk văn bản. |

---

## 🧪 6. Kết quả Kiểm thử Thực tế & Cầu nối sang Ngày 6

Kịch bản kiểm thử toàn diện tại [`test/test_chroma_store.py`](file:///c:/Users/Nguyen%20Duc%20Vu%20Bao/Desktop/RAG/test/test_chroma_store.py) đã chạy và vượt qua **4/4 bài kiểm thử**:

```text
=====================================================================
🚀 BẮT ĐẦU KIỂM THỬ TOÀN DIỆN CHROMADB VECTOR STORE (NGÀY 5)
=====================================================================

--- BÀI TEST 1: KHỞI TẠO VÀ THÊM DỮ LIỆU VÀO CHROMADB ---
[INFO] - Đang tạo vector embedding cho 5 chunks...
[INFO] - Đã lưu thành công 5 chunks vào ChromaDB.
[INFO] - Tổng số bản ghi trong ChromaDB hiện tại: 5
✅ Bài test 1: Ingestion và Count thành công 100%!

--- BÀI TEST 2: TRUY VẤN NGỮ NGHĨA TOP-K BẰNG CÂU HỎI TỰ NHIÊN ---
[INFO] - Câu hỏi của học viên: 'How to talk about things I have experienced in my life?'
[INFO] - Top 1 | Điểm tương đồng: 0.6337 (Distance: 0.3663)
         Nguồn: [English Grammar in Use - Trang 14]
         Nội dung: "The present perfect tense is formed with have/has + past participle (V3)..."
✅ Bài test 2: Semantic Search xếp hạng chính xác 100%!

--- BÀI TEST 3: TÌM KIẾM KẾT HỢP BỘ LỌC METADATA ---
[INFO] - Câu hỏi: 'How to use past participle V3?' với điều kiện: {'book_title': 'Oxford Practice Grammar'}
[INFO] - Top 1 | Sách: Oxford Practice Grammar | Điểm: 0.7698
         Nội dung: "Passive voice is formed with 'be' + past participle (V3)..."
✅ Bài test 3: Metadata Filtering hoạt động chính xác tuyệt đối!

--- BÀI TEST 4: KIỂM CHỨNG LƯU TRỮ BỀN VỮNG XUỐNG Ổ CỨNG ---
[INFO] - Giả lập tắt ứng dụng và khởi động lại Client mới kết nối vào thư mục...
[INFO] - Số lượng bản ghi tự động nạp từ ổ cứng: 5
[INFO] - Kết quả truy vấn tức thì từ đĩa: "Use 'since' with a specific point in time..."
✅ Bài test 4: Tính bền vững (Persistence) hoạt động hoàn hảo!

🎉 TOÀN BỘ 4 BÀI TEST ĐÃ VƯỢT QUA XUẤT SẮC!
```

---

### 🚀 Cầu nối sang Ngày 6 (Xây dựng RAG Engine & Grounded Prompting)
- **Đã hoàn thành**: Đến Ngày 5, chúng ta đã có đủ 3 mảnh ghép nền tảng độc lập:
  1. `DocumentService`: Đọc & trích xuất PDF tiếng Anh.
  2. `ChunkerService`: Băm nhỏ văn bản kèm metadata.
  3. `ChromaVectorStore`: Lưu trữ vector bền vững và tìm kiếm Top-k siêu tốc.
- **Mục tiêu Ngày 6**: Nối toàn bộ các module trên lại thành một hệ thống hoàn chỉnh thông qua **Facade Pattern (`RAGService`)**:
  - Nhận câu hỏi của học viên $\rightarrow$ Truy vấn Top-k chunks từ ChromaDB $\rightarrow$ Thiết kế **Grounded System Prompt** chống ảo giác (Hallucination) $\rightarrow$ Gửi tới Gemini 1.5 Flash $\rightarrow$ Trả về câu trả lời chuẩn xác kèm trích dẫn nguồn!
