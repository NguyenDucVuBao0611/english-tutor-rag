import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ Không tìm thấy GEMINI_API_KEY trong file .env!")

client = genai.Client(api_key=api_key)



def test_llm_chat():
    print("\n--- 1. TEST LLM (ENGLISH TUTOR) ---")
    system_instruction = (
        "Bạn là một Gia sư Tiếng Anh (English Tutor) thông thái và thân thiện. "
        "Nhiệm vụ của bạn là giải thích ngắn gọn, dễ hiểu ngữ pháp và từ vựng tiếng Anh "
        "bằng tiếng Việt, kèm theo ví dụ chuẩn tiếng Anh."
    )
    prompt = "Giải thích ngắn gọn sự khác nhau giữa 'Present Perfect' và 'Past Simple'."
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
    )
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=config,
    )
    print(response.text)


def test_embedding():
    print("\n--- 2. TEST EMBEDDING ---")
    sample_text = "The present perfect tense is used for actions completed at an unspecified time."
    
    # Model embedding từ danh sách khả dụng
    embed_model = "gemini-embedding-001"
    
    try:
        embedding_response = client.models.embed_content(
            model=embed_model,
            contents=sample_text,
        )
    except Exception as e:
        print(f"Thử lại với gemini-embedding-2 do: {e}")
        embed_model = "gemini-embedding-2"
        embedding_response = client.models.embed_content(
            model=embed_model,
            contents=sample_text,
        )
    
    embedding_vector = embedding_response.embeddings[0].values
    vector_dim = len(embedding_vector)
    
    print(f"Model: {embed_model}")
    print(f"Câu mẫu: '{sample_text}'")
    print(f"Số chiều vector (Dimension): {vector_dim}")
    print(f"5 giá trị đầu tiên của vector: {embedding_vector[:5]}")
    print("\n✅ Ngày 1: Kết nối API và thiết lập môi trường thành công!")


if __name__ == "__main__":
    test_llm_chat()
    test_embedding()



