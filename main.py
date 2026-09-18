import os
from typing import Annotated, Dict, List, Sequence, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from toolsplus import generate_quiz_from_json, prepare_quiz_data_from_pdf, submit_quiz


load_dotenv()


class TutorAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


tools = [prepare_quiz_data_from_pdf, generate_quiz_from_json, submit_quiz]

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
).bind_tools(tools)


def model_call(state: TutorAgentState) -> Dict[str, List[BaseMessage]]:
    system_prompt = SystemMessage(
        content=(
            "You are a Vietnamese learning tutor.\n\n"
            "Tool usage rules:\n"
            "- When the user asks to process, read, chunk, or run chunker on a "
            "PDF, call prepare_quiz_data_from_pdf first.\n"
            "- When the user asks to create, generate, or make a quiz, call "
            "generate_quiz_from_json.\n"
            "- Never reveal answers while presenting a newly generated quiz. The "
            "user must submit answers later using question IDs and option letters.\n"
            "- When the user submits quiz answers, call submit_quiz. Then report "
            "the score and provide the material_to_review and source_pages for "
            "every wrong question.\n"
            "- If the user asks to process a PDF and create a quiz, call "
            "prepare_quiz_data_from_pdf first, then call "
            "generate_quiz_from_json using the json_file_path returned by the "
            "first tool.\n"
            "- Use output/knowledge_output.json as json_file_path unless the "
            "user explicitly provides another JSON path.\n"
            "- Infer number_of_questions from the request; use 5 when omitted.\n"
            "- After the tool returns, present the quiz clearly in Vietnamese.\n"
            "- Do not invent quiz content before calling the tool.\n"
            "- For normal learning questions, answer conversationally and do not "
            "call the quiz tool."
        )
    )
    response = llm.invoke([system_prompt] + list(state["messages"]))
    return {"messages": [response]}


def should_continue(state: TutorAgentState) -> str:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "continue"
    return "end"


graph = StateGraph(TutorAgentState)
graph.add_node("tutor", model_call)
graph.add_node("tools", ToolNode(tools=tools))
graph.set_entry_point("tutor")
graph.add_conditional_edges(
    "tutor",
    should_continue,
    {"continue": "tools", "end": END},
)
graph.add_edge("tools", "tutor")

tutor_agent = graph.compile()


def extract_text_response(messages: Sequence[BaseMessage]) -> str:
    for message in reversed(messages):
        if not isinstance(message, AIMessage):
            continue
        if isinstance(message.content, str) and message.content.strip():
            return message.content.strip()
        if isinstance(message.content, list):
            text_parts = [
                block["text"]
                for block in message.content
                if isinstance(block, dict)
                and block.get("type") == "text"
                and block.get("text", "").strip()
            ]
            if text_parts:
                return " ".join(text_parts).strip()
    return "(Không có phản hồi)"


def run_chat() -> None:
    print("ORBITA Learning Tutor")
    print("=" * 40)
    print("Nhập 'exit' để thoát.\n")

    conversation_messages: List[BaseMessage] = []
    while True:
        try:
            user_input = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "thoát"}:
            print("Tạm biệt!")
            break

        conversation_messages.append(HumanMessage(content=user_input))
        result = tutor_agent.invoke(
            {"messages": conversation_messages},
            config={"recursion_limit": 10},
        )
        result_messages = list(result["messages"])
        new_messages = result_messages[len(conversation_messages):]
        conversation_messages.extend(new_messages)
        print(f"Agent: {extract_text_response(new_messages)}\n")


if __name__ == "__main__":
    run_chat()