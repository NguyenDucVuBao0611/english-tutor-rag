import sys
from pathlib import Path
import numpy as np

# Đảm bảo thư mục gốc dự án luôn nằm trong sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.logger import logger
from src.services.embedding_service import EmbeddingService


# =====================================================================
# 1. CÁC HÀM TOÁN HỌC THUẦN TÚY BẰNG NUMPY (VECTOR SIMILARITY)
# =====================================================================

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Tính độ tương đồng Cosine giữa 2 vector số thực.

    Công thức: Cos(theta) = (u . v) / (||u|| * ||v||)

    Args:
        vec1 (np.ndarray): Vector thứ nhất (1 chiều).
        vec2 (np.ndarray): Vector thứ hai (1 chiều).

    Returns:
        float: Giá trị Cosine trong đoạn [-1.0, 1.0]. Càng gần 1.0 càng đồng nghĩa.
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def matrix_cosine_similarity(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
    """Tính độ tương đồng Cosine giữa 1 query vector và hàng ngàn chunk cùng 1 lúc bằng MA TRẬN.

    Args:
        query_vec (np.ndarray): Vector câu hỏi (kích thước: [D]).
        doc_matrix (np.ndarray): Ma trận chứa N vectors tài liệu (kích thước: [N, D]).

    Returns:
        np.ndarray: Mảng 1 chiều gồm N điểm số tương đồng tương ứng với từng tài liệu.
    """
    # 1. Chuẩn hóa độ dài vector câu hỏi về 1 (Unit Vector)
    q_norm = query_vec / np.linalg.norm(query_vec)

    # 2. Chuẩn hóa độ dài từng hàng trong ma trận tài liệu về 1 (theo trục ngang axis=1)
    doc_norms = doc_matrix / np.linalg.norm(doc_matrix, axis=1, keepdims=True)

    # 3. Nhân ma trận 1 phát ra ngay toàn bộ điểm số: Scores = Matrix * Query^T
    scores = np.dot(doc_norms, q_norm)
    return scores


# =====================================================================
# 2. CÁC BÀI KIỂM THỬ THỰC TẾ
# =====================================================================

def test_math_properties():
    """Kiểm tra tính đúng đắn toán học của hàm Cosine Similarity."""
    logger.info("=== BÀI TEST 1: CHỨNG MINH TÍNH CHẤT TOÁN HỌC CỦA COSINE SIMILARITY ===")

    v_base = np.array([1.0, 2.0, 3.0])

    # 1. Hai vector cùng hướng hoàn toàn -> Góc 0 độ -> Cosine = 1.0
    v_same = np.array([2.0, 4.0, 6.0])  # Gấp đôi v_base
    sim_same = cosine_similarity(v_base, v_same)
    logger.info(f"1. Cùng hướng (θ = 0°): Cosine = {sim_same:.4f} (Kỳ vọng: 1.0000)")
    assert np.isclose(sim_same, 1.0), "Lỗi: Hai vector cùng hướng nhưng Cosine != 1.0"

    # 2. Hai vector vuông góc -> Góc 90 độ -> Cosine = 0.0 (Hoàn toàn không liên quan)
    v_ortho = np.array([-2.0, 1.0, 0.0])  # Tích vô hướng: 1*(-2) + 2*1 + 3*0 = 0
    sim_ortho = cosine_similarity(v_base, v_ortho)
    logger.info(f"2. Vuông góc (θ = 90°): Cosine = {sim_ortho:.4f} (Kỳ vọng: 0.0000)")
    assert np.isclose(sim_ortho, 0.0), "Lỗi: Hai vector vuông góc nhưng Cosine != 0.0"

    # 3. Hai vector ngược hướng -> Góc 180 độ -> Cosine = -1.0 (Đối lập hoàn toàn)
    v_opposite = np.array([-1.0, -2.0, -3.0])
    sim_opp = cosine_similarity(v_base, v_opposite)
    logger.info(f"3. Ngược hướng (θ = 180°): Cosine = {sim_opp:.4f} (Kỳ vọng: -1.0000)")
    assert np.isclose(sim_opp, -1.0), "Lỗi: Hai vector ngược hướng nhưng Cosine != -1.0"

    logger.info("✅ Bài test 1: Các định luật toán học hoạt động chuẩn xác 100%!")


def test_real_semantic_search():
    """Kiểm thử tìm kiếm ngữ nghĩa AI thực tế với Google Gemini Embeddings và NumPy."""
    logger.info("=== BÀI TEST 2: THỰC CHIẾN TÌM KIẾM NGỮ NGHĨA BẰNG NUMPY ===")

    # 1. Kho tài liệu mẫu gồm 4 đoạn văn bản khác nhau
    documents = [
        "The present perfect tense is formed with have/has + past participle (V3). It connects the past with the present.",
        "The past continuous tense uses was/were + V-ing to describe actions happening at a specific time in the past.",
        "Future simple with 'will' is used for promises, offers, and decisions made at the moment of speaking.",
        "Photosynthesis is the biological process used by green plants to convert light energy into chemical energy.",
    ]

    # 2. Câu hỏi của học viên (Cố tình dùng từ ngữ khác để thử tìm kiếm ngữ nghĩa)
    query = "How do I use have and has with V3 to talk about life experience?"

    logger.info(f"Câu hỏi của học viên: '{query}'")
    logger.info(f"Đang vector hóa câu hỏi và {len(documents)} tài liệu qua Gemini Embedding...")

    embed_service = EmbeddingService()

    # Tạo vector cho câu hỏi và các tài liệu
    query_vec = np.array(embed_service.embed_text(query))
    doc_vectors = np.array(embed_service.embed_batch(documents))

    logger.info(f"Số chiều của Vector: {query_vec.shape[0]} chiều")

    # 3. Tính toán độ tương đồng ma trận bằng 1 dòng lệnh NumPy duy nhất!
    scores = matrix_cosine_similarity(query_vec, doc_vectors)

    # 4. Sắp xếp thứ tự từ cao nhất đến thấp nhất (Top-k Ranking)
    ranked_indices = np.argsort(scores)[::-1]

    logger.info("--- BẢNG XẾP HẠNG KẾT QUẢ TÌM KIẾM (TOP-K) ---")
    for rank, idx in enumerate(ranked_indices):
        score = scores[idx]
        doc_text = documents[idx]
        logger.info(f"Top {rank + 1} [Điểm: {score:.4f}]: \"{doc_text[:80]}...\"")

    # Kiểm tra xem tài liệu số 0 (Hiện tại hoàn thành) có giành ngôi đầu bảng không
    assert ranked_indices[0] == 0, "Lỗi: Thuật toán không đưa đoạn Hiện tại hoàn thành lên Top 1!"

    logger.info("✅ Bài test 2: NumPy đã xếp hạng chính xác đoạn văn ngữ pháp liên quan nhất lên Top 1!")


if __name__ == "__main__":
    test_math_properties()
    print()
    test_real_semantic_search()
