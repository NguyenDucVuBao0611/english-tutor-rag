import sys
import os
from pathlib import Path

# Đảm bảo thư mục gốc nằm trong sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.logger import logger
from src.agents.tutor_agent import TutorAgent
from src.tools.rag_tool import GrammarRetrievalTool
from src.services.rag_service import RAGService
from src.vector_store.chroma_store import ChromaVectorStore


def print_banner():
    banner = """
================================================================================
   🎓 ENTERPRISE AI ENGLISH TUTOR AGENT - INTERACTIVE CLI (MILESTONE 1)
================================================================================
   * Mô hình Agent: Autonomous ReAct (Reasoning + Acting)
   * Kho tri thức: ChromaDB Persistent Vector Store + Gemini LLM
   * Hướng dẫn:
     - Gõ câu hỏi ngữ pháp, câu giao tiếp hoặc câu cần sửa lỗi.
     - Gõ 'thought' sau câu trả lời để xem lại nhật ký suy luận của Agent.
     - Gõ 'exit' hoặc 'quit' để thoát chương trình.
================================================================================
"""
    print(banner)


def main():
    print_banner()

    print("⏳ Đang khởi động hệ thống Gia Sư AI và nạp cơ sở dữ liệu ChromaDB...")
    try:
        vector_store = ChromaVectorStore()
        rag_service = RAGService(vector_store=vector_store)
        grammar_tool = GrammarRetrievalTool(rag_service=rag_service)
        agent = TutorAgent(tools=[grammar_tool])
        print("✅ Hệ thống đã sẵn sàng! Bạn có thể bắt đầu trò chuyện với Thầy/Cô AI.\n")
    except Exception as e:
        print(f"❌ Lỗi khi khởi động Agent: {e}")
        return

    last_response = None

    while True:
        try:
            user_input = input("👤 Bạn: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\n👋 Tạm biệt bạn! Chúc bạn học tiếng Anh thật tốt. Hẹn gặp lại!")
                break

            if user_input.lower() == "thought":
                if last_response and last_response.get("thought_trajectory"):
                    print("\n🧠 --- NHẬT KÝ SUY LUẬN GẦN NHẤT CỦA AGENT ---")
                    for s in last_response["thought_trajectory"]:
                        print(f"  [Bước {s.get('step')}]:")
                        print(f"    - Thought: {s.get('thought')}")
                        if "action" in s:
                            print(f"    - Action: {s.get('action')} (Tham số: {s.get('action_input')})")
                            print(f"    - Observation: {s.get('observation')[:100]}...")
                    print("------------------------------------------------\n")
                else:
                    print("Chưa có nhật ký suy luận nào trước đó.\n")
                continue

            if user_input.lower() == "clear":
                os.system("cls" if os.name == "nt" else "clear")
                print_banner()
                continue

            print("\n🤖 Gia Sư AI đang suy nghĩ...", end="\r", flush=True)
            response = agent.chat(user_message=user_input)
            last_response = response

            # Xóa dòng "đang suy nghĩ"
            print(" " * 50, end="\r", flush=True)

            print(f"🤖 Gia Sư AI:\n{response['answer']}\n")

            if response.get("tools_used"):
                tools_str = ", ".join(response["tools_used"])
                print(f"💡 [Hệ thống: Agent đã kích hoạt công cụ: '{tools_str}']")

            if response.get("sources"):
                sources_str = ", ".join(
                    [f"[{s.get('book_title')} - Trang {s.get('page_number')}]" for s in response["sources"]]
                )
                print(f"📖 [Nguồn trích dẫn: {sources_str}]\n")

        except KeyboardInterrupt:
            print("\n👋 Đã dừng chương trình. Tạm biệt!")
            break
        except Exception as e:
            print(f"\n❌ Đã xảy ra lỗi: {e}\n")


if __name__ == "__main__":
    main()
