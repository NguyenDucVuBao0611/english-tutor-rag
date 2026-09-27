import json
import re
from typing import Any, Dict, List, Optional

from src.core.logger import logger
from src.services.llm_service import LLMService
from src.tools.base import BaseTool
from src.tools.rag_tool import GrammarRetrievalTool


AGENT_SYSTEM_PROMPT = """Bạn là một Gia Sư Tiếng Anh Tự Trị (Autonomous AI English Tutor Agent) thông minh, kiên nhẫn và giàu kinh nghiệm sư phạm.

BẠN CÓ QUYỀN SỬ DỤNG CÁC CÔNG CỤ (TOOLS) SAU ĐÂY:
{tools_description}

QUY TRÌNH SUY LUẬN ReAct (REASONING + ACTING):
Khi nhận được tin nhắn của học viên, bạn BẮT BUỘC phải thực hiện suy nghĩ và tuân thủ đúng định dạng sau:

NẾU CÂU NÓI LÀ CHÀO HỎI, XÃ GIAO HOẶC CÂU CẢM ƠN (Không liên quan đến kiến thức tiếng Anh cụ thể):
Bạn KHÔNG ĐƯỢC gọi công cụ tra cứu. Hãy trả lời ngay lập tức theo định dạng:
Thought: Đây là câu giao tiếp xã giao thông thường, không cần tra cứu giáo trình.
Final Answer: [Lời chào hoặc câu đáp thân thiện bằng tiếng Anh và tiếng Việt]

NẾU CÂU HỎI LIÊN QUAN ĐẾN NGỮ PHÁP, TỪ VỰNG, CẤU TRÚC HOẶC BÀI TẬP:
Bạn phải tra cứu giáo trình trước khi trả lời theo đúng định dạng sau:
Thought: [Phân tích câu hỏi của học viên và nêu rõ lý do tại sao cần tra cứu]
Action: [Tên chính xác của công cụ muốn dùng]
Action Input: {{"tham_so": "gia_tri"}}

Sau đó, hệ thống sẽ trả lại kết quả dưới dạng:
Observation: [Nội dung trích đoạn từ giáo trình]

Dựa vào Observation, bạn suy nghĩ tiếp:
Thought: [Tôi đã có đủ thông tin từ giáo trình để giảng giải cho học viên]
Final Answer: [Câu trả lời sư phạm chi tiết bằng tiếng Việt, ví dụ chuẩn tiếng Anh, và BẮT BUỘC ghi rõ 📚 Nguồn tham khảo: [Tên sách - Trang]]

LƯU Ý QUAN TRỌNG:
- Sau mỗi 'Action Input:', BẮT BUỘC dừng lại và đợi kết quả 'Observation:'.
- Khi đã có câu trả lời cuối cùng, PHẢI bắt đầu bằng 'Final Answer:'.
- Tuyệt đối không tự bịa đặt cấu trúc ngữ pháp nếu không có trong Observation."""


class TutorAgent:
    """Gia sư Tiếng Anh Tự Trị vận hành theo vòng lặp ReAct (Reasoning + Acting).
    
    Tự chủ phân loại ý định (Intent Routing), quyết định kích hoạt công cụ tra cứu
    và tổng hợp lời giảng sư phạm chuẩn xác có căn cứ.
    """

    def __init__(
        self,
        tools: Optional[List[BaseTool]] = None,
        llm_service: Optional[LLMService] = None,
    ) -> None:
        """Khởi tạo TutorAgent với danh sách công cụ và LLM Service."""
        self.llm_service = llm_service or LLMService()
        
        # Mặc định trang bị công cụ GrammarRetrievalTool nếu không truyền vào
        if tools is None:
            self.tools = [GrammarRetrievalTool()]
        else:
            self.tools = tools

        self.tools_map: Dict[str, BaseTool] = {tool.name: tool for tool in self.tools}
        self.system_prompt = self._build_system_prompt()
        logger.info(f"Khởi tạo thành công TutorAgent với {len(self.tools)} công cụ: {list(self.tools_map.keys())}")

    def _build_system_prompt(self) -> str:
        """Tạo bản mô tả chi tiết danh sách công cụ cho Prompt hệ thống."""
        tool_descs: List[str] = []
        for tool in self.tools:
            schema = tool.args_schema.model_json_schema()
            params = schema.get("properties", {})
            param_desc = ", ".join([f"{k}: {v.get('description', '')}" for k, v in params.items()])
            tool_descs.append(f"- **{tool.name}**: {tool.description}\n  Tham số: {{{param_desc}}}")

        return AGENT_SYSTEM_PROMPT.format(tools_description="\n".join(tool_descs))

    def chat(self, user_message: str, max_iterations: int = 4) -> Dict[str, Any]:
        """Thực thi chu trình ReAct xử lý câu hỏi của học viên.

        Args:
            user_message (str): Câu hỏi hoặc lời trò chuyện của học viên.
            max_iterations (int): Số vòng lặp suy luận tối đa để tránh lặp vô tận.

        Returns:
            Dict[str, Any]: Kết quả gồm:
                - answer (str): Câu trả lời cuối cùng cho học viên.
                - thought_trajectory (List[Dict]): Toàn bộ nhật ký suy luận (Thought, Action, Observation).
                - tools_used (List[str]): Danh sách các công cụ đã được kích hoạt.
                - sources (List[Dict]): Nguồn sách trích dẫn (nếu có dùng RAG tool).
        """
        logger.info(f"\n=======================================================")
        logger.info(f"🤖 [TUTOR AGENT] TIẾP NHẬN YÊU CẦU: '{user_message}'")
        logger.info(f"=======================================================")

        trajectory: List[Dict[str, Any]] = []
        tools_called: List[str] = []
        collected_sources: List[Dict[str, Any]] = []

        # Lịch sử hội thoại của vòng lặp ReAct
        prompt_history = f"Học viên: {user_message}\n"

        for step in range(1, max_iterations + 1):
            logger.info(f"--- Vòng lặp suy luận {step}/{max_iterations} ---")

            full_prompt = f"{prompt_history}\nHãy suy nghĩ và thực hiện bước tiếp theo:"
            response_text = self.llm_service.generate_text(
                prompt=full_prompt,
                system_instruction=self.system_prompt,
                temperature=0.1,  # Nhiệt độ thấp đảm bảo tuân thủ đúng cú pháp Action
            )

            logger.info(f"[Agent Raw Output]:\n{response_text}")

            # 1. Kiểm tra xem Agent đã đưa ra Final Answer chưa
            if "Final Answer:" in response_text:
                final_answer = response_text.split("Final Answer:")[-1].strip()
                thought_match = re.search(r"Thought:\s*(.*?)(?=Final Answer:|$)", response_text, re.DOTALL)
                thought = thought_match.group(1).strip() if thought_match else "Đã hoàn thành câu trả lời."
                
                trajectory.append({"step": step, "thought": thought, "final_answer": final_answer})
                logger.info(f"✅ Agent đã đưa ra câu trả lời cuối cùng tại bước {step}.")
                
                # Thu thập sources từ RAG tool nếu có
                for tool in self.tools:
                    if hasattr(tool, "last_retrieved_sources") and tool.last_retrieved_sources:
                        collected_sources.extend(tool.last_retrieved_sources)

                return {
                    "answer": final_answer,
                    "thought_trajectory": trajectory,
                    "tools_used": list(set(tools_called)),
                    "sources": collected_sources,
                }

            # 2. Bóc tách Action và Action Input nếu Agent muốn gọi Tool
            action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)", response_text)
            action_input_match = re.search(r"Action Input:\s*(\{.*?\})", response_text, re.DOTALL)

            thought_match = re.search(r"Thought:\s*(.*?)(?=Action:|$)", response_text, re.DOTALL)
            thought_text = thought_match.group(1).strip() if thought_match else "Đang phân tích..."

            if action_match and action_input_match:
                tool_name = action_match.group(1).strip()
                input_str = action_input_match.group(1).strip()

                try:
                    tool_args = json.loads(input_str)
                except json.JSONDecodeError:
                    # Dự phòng nếu LLM sinh json thiếu ngoặc kép
                    tool_args = {"query": user_message}

                logger.info(f"⚡ [Agent Quyết Định Gọi Tool]: '{tool_name}' với tham số: {tool_args}")
                tools_called.append(tool_name)

                # 3. Thực thi Tool
                if tool_name in self.tools_map:
                    try:
                        observation = self.tools_map[tool_name].execute(**tool_args)
                    except Exception as e:
                        observation = f"Lỗi khi thực thi công cụ '{tool_name}': {str(e)}"
                else:
                    observation = f"Lỗi: Không tìm thấy công cụ '{tool_name}' trong danh sách cho phép."

                logger.info(f"👁️ [Observation từ Tool]:\n{observation[:150]}...")

                trajectory.append(
                    {
                        "step": step,
                        "thought": thought_text,
                        "action": tool_name,
                        "action_input": tool_args,
                        "observation": observation,
                    }
                )

                # Nối tiếp kết quả Observation vào hội thoại để vòng lặp sau LLM đọc tiếp
                prompt_history += (
                    f"\nThought: {thought_text}\n"
                    f"Action: {tool_name}\n"
                    f"Action Input: {json.dumps(tool_args)}\n"
                    f"Observation: {observation}\n"
                )
            else:
                # Nếu LLM không gọi tool và cũng không viết Final Answer rõ ràng, lấy toàn bộ làm câu trả lời
                clean_answer = response_text.replace("Thought:", "").strip()
                trajectory.append({"step": step, "thought": "Trực tiếp phản hồi", "final_answer": clean_answer})
                return {
                    "answer": clean_answer,
                    "thought_trajectory": trajectory,
                    "tools_used": list(set(tools_called)),
                    "sources": collected_sources,
                }

        # Nếu đạt số lần lặp tối đa mà chưa ra Final Answer
        fallback_msg = "Xin lỗi bạn, tôi đã vượt quá số bước suy luận cho phép mà chưa thể hoàn tất lời giảng."
        return {
            "answer": fallback_msg,
            "thought_trajectory": trajectory,
            "tools_used": list(set(tools_called)),
            "sources": collected_sources,
        }
