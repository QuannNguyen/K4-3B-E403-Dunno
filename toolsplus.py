import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv

from src.chunker import pdf_to_json

load_dotenv()

try:
    from langchain.tools import tool
except ImportError:
    def tool(function):
        function.invoke = lambda arguments: function(**arguments)
        return function


def _load_concepts(json_file_path: str) -> List[Dict[str, Any]]:
    path = Path(json_file_path)
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        concepts = data
    elif isinstance(data, dict):
        concepts = data.get("concepts", [])
    else:
        concepts = []

    valid_concepts = [
        concept for concept in concepts
        if isinstance(concept, dict)
        and str(concept.get("name", "")).strip()
        and str(concept.get("definition", "")).strip()
    ]
    if not valid_concepts:
        raise ValueError("JSON must contain at least one concept with name and definition")
    return valid_concepts


def _fallback_quiz(concepts: List[Dict[str, Any]], number_of_questions: int) -> List[Dict[str, Any]]:
    questions = []
    selected = concepts[:number_of_questions]
    names = [str(concept["name"]).strip() for concept in concepts]

    for index, concept in enumerate(selected, start=1):
        correct_answer = str(concept["definition"]).strip()
        distractors = [
            name for name in names
            if name.lower() != str(concept["name"]).strip().lower()
        ][:3]
        options = [correct_answer] + distractors
        options = options[:4]
        questions.append({
            "id": index,
            "type": "multiple_choice",
            "question": f"Nội dung nào mô tả đúng nhất về {concept['name']}?",
            "options": options,
            "answer": correct_answer,
            "explanation": correct_answer,
            "source_pages": concept.get("source_pages", []),
            "concept_id": concept.get("id"),
        })
    return questions


def _llm_quiz(
    concepts: List[Dict[str, Any]],
    number_of_questions: int,
    difficulty: str,
    language: str,
) -> List[Dict[str, Any]]:
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        return []

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return []

    model = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        api_key=api_key,
        temperature=0.3,
    )
    prompt_concepts = [
        {
            "id": concept.get("id"),
            "name": str(concept.get("name", ""))[:160],
            "definition": str(concept.get("definition", ""))[:500],
            "source_pages": concept.get("source_pages", []),
        }
        for concept in concepts[:max(number_of_questions * 3, 10)]
    ]
    prompt = {
        "instruction": (
            "Create a study quiz from the supplied concepts. Return JSON only, "
            "with a top-level 'questions' array. Each question must have: id, "
            "type='multiple_choice', question, options (exactly 4 strings), "
            "answer, explanation, source_pages, and concept_id. Do not use facts "
            "outside the supplied content."
        ),
        "language": language,
        "difficulty": difficulty,
        "number_of_questions": number_of_questions,
        "concepts": prompt_concepts,
    }
    try:
        response = model.invoke(json.dumps(prompt, ensure_ascii=False))
    except Exception:
        return []
    content = response.content if isinstance(response.content, str) else str(response.content)
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return []

    parsed = json.loads(match.group(0))
    questions = parsed.get("questions", [])
    if not isinstance(questions, list):
        return []
    return questions[:number_of_questions]


def _option_letter(options: List[Any], answer: Any) -> str:
    answer_text = str(answer).strip().lower()
    for index, option in enumerate(options):
        if answer_text == str(option).strip().lower():
            return chr(65 + index)
    if len(answer_text) == 1 and answer_text in "abcd":
        return answer_text.upper()
    return ""


def _save_quiz_files(
    questions: List[Dict[str, Any]],
    output_txt_path: str,
    answer_key_path: str,
) -> str:
    output_path = Path(output_txt_path)
    key_path = Path(answer_key_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    quiz_lines = ["QUIZ ÔN TẬP", "=" * 40, ""]
    answer_key = []

    for index, question in enumerate(questions, start=1):
        question_id = str(question.get("id", index))
        options = question.get("options", [])
        quiz_lines.append(f"Câu {index}: {question.get('question', '')}")
        for option_index, option in enumerate(options, start=1):
            quiz_lines.append(f"  {chr(64 + option_index)}. {option}")
        quiz_lines.append("")
        answer_key.append({
            "id": question_id,
            "answer": _option_letter(options, question.get("answer", "")),
            "concept_id": question.get("concept_id"),
            "concept_name": question.get("concept_name", question.get("question", "")),
            "explanation": question.get("explanation", ""),
            "source_pages": question.get("source_pages", []),
            "material": question.get("material", question.get("explanation", "")),
        })

    output_path.write_text("\n".join(quiz_lines), encoding="utf-8")
    key_path.write_text(
        json.dumps({"questions": answer_key}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(output_path)


@tool
def prepare_quiz_data_from_pdf(
    pdf_file_path: str,
    output_json_path: str = "output/knowledge_output.json",
    max_chars: int = 3000,
) -> Dict[str, Any]:
    """Run the PDF chunker and save quiz-ready knowledge JSON.

    Call this before generating a quiz when the user provides a PDF or asks
    to process a PDF first. The returned JSON path can be passed to
    generate_quiz_from_json.
    """
    if not pdf_file_path.lower().endswith(".pdf"):
        raise ValueError("pdf_file_path must point to a PDF file")

    result = pdf_to_json(
        pdf_path=pdf_file_path,
        output_path=output_json_path,
        max_chars=max_chars,
    )
    return {
        "status": result["status"],
        "pdf_file_path": pdf_file_path,
        "json_file_path": output_json_path,
        "page_count": result["page_count"],
        "chunk_count": result["chunk_count"],
        "concept_count": len(result["concepts"]),
        "message": "PDF đã được chuyển thành dữ liệu sẵn sàng để tạo quiz.",
    }


@tool
def generate_quiz_from_json(
    json_file_path: str,
    number_of_questions: int = 5,
    difficulty: str = "mixed",
    language: str = "Vietnamese",
    output_txt_path: str = "output/quiz.txt",
    answer_key_path: str = "output/quiz_key.json",
) -> Dict[str, Any]:
    """Generate a multiple-choice study quiz from a knowledge JSON file.

    The JSON can be the project's knowledge_output.json or a plain list of
    concept objects. When GROQ_API_KEY is available, an LLM creates the quiz;
    otherwise a deterministic quiz is generated from each concept definition.
    """
    if not 1 <= number_of_questions <= 50:
        raise ValueError("number_of_questions must be between 1 and 50")

    concepts = _load_concepts(json_file_path)
    number_of_questions = min(number_of_questions, len(concepts))
    questions = _llm_quiz(concepts, number_of_questions, difficulty, language)
    generation_method = "llm" if questions else "fallback"
    if not questions:
        questions = _fallback_quiz(concepts, number_of_questions)
    for question in questions:
        concept_id = question.get("concept_id")
        concept = next((item for item in concepts if item.get("id") == concept_id), None)
        if concept:
            question.setdefault("concept_name", concept.get("name", ""))
            question.setdefault("material", concept.get("definition", ""))
            question.setdefault("source_pages", concept.get("source_pages", []))
    saved_txt_path = _save_quiz_files(questions, output_txt_path, answer_key_path)

    return {
        "status": "success",
        "source_file": json_file_path,
        "question_count": len(questions),
        "difficulty": difficulty,
        "language": language,
        "generation_method": generation_method,
        "output_txt_path": saved_txt_path,
        "answer_key_path": answer_key_path,
        "questions": [
            {
                key: value
                for key, value in question.items()
                if key not in {"answer", "explanation", "material"}
            }
            for question in questions
        ],
    }


@tool
def submit_quiz(
    answers: Dict[str, str],
    answer_key_path: str = "output/quiz_key.json",
) -> Dict[str, Any]:
    """Grade a submitted quiz and return targeted review material for mistakes.

    Answers should map question IDs to option letters, for example:
    {"1": "B", "2": "A"}.
    """
    key_path = Path(answer_key_path)
    if not key_path.is_file():
        raise FileNotFoundError("Chưa tìm thấy đáp án quiz. Hãy tạo quiz trước.")
    if not isinstance(answers, dict):
        raise ValueError("answers phải là object dạng {'1': 'A', '2': 'B'}")

    answer_data = json.loads(key_path.read_text(encoding="utf-8"))
    wrong_answers = []
    correct_count = 0
    questions = answer_data.get("questions", [])
    for item in questions:
        question_id = str(item.get("id"))
        submitted = str(answers.get(question_id, "")).strip().upper()
        expected = str(item.get("answer", "")).strip().upper()
        if submitted == expected:
            correct_count += 1
        else:
            wrong_answers.append({
                "question_id": question_id,
                "your_answer": submitted or None,
                "correct_answer": expected,
                "concept_id": item.get("concept_id"),
                "concept_name": item.get("concept_name"),
                "source_pages": item.get("source_pages", []),
                "material_to_review": item.get("material", ""),
                "explanation": item.get("explanation", ""),
            })

    return {
        "status": "graded",
        "score": correct_count,
        "total": len(questions),
        "wrong_count": len(wrong_answers),
        "wrong_questions": wrong_answers,
        "message": (
            "Bạn hãy ôn lại tài liệu ở source_pages của các câu sai."
            if wrong_answers else "Chúc mừng, bạn đã trả lời đúng tất cả câu hỏi!"
        ),
    }


if __name__ == "__main__":
    result = generate_quiz_from_json.invoke({
        "json_file_path": "output/knowledge_output.json",
        "number_of_questions": 5,
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))