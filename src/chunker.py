import json
import re
from pathlib import Path

from src.parser import read_pdf


def chunk_pages(pages, max_chars=3000):
    """Split extracted PDF pages into text chunks while preserving page numbers."""
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")

    chunks = []

    current_text = ""
    current_pages = []

    for page in pages:

        page_text = str(page.get("text", "")).strip()
        if not page_text:
            continue

        if current_text and len(current_text) + len(page_text) > max_chars:
            chunks.append({
                "text": current_text.strip(),
                "pages": current_pages
            })

            current_text = ""
            current_pages = []

        current_text += page_text + "\n"
        current_pages.append(page["page"])

    if current_text:
        chunks.append({
            "text": current_text.strip(),
            "pages": current_pages
        })

    return chunks


def extract_concepts(chunks, max_concepts_per_chunk=5):
    """Create quiz-ready concept records from chunk text without an API call."""
    concepts = []
    for chunk in chunks:
        sentences = [
            sentence.strip(" -:;\t\r\n")
            for sentence in re.split(r"(?<=[.!?])\s+|\n+", chunk["text"])
            if len(sentence.strip()) >= 20
        ]

        for sentence in sentences[:max_concepts_per_chunk]:
            concepts.append({
                "id": f"concept-{len(concepts) + 1}",
                "name": sentence[:80].strip(),
                "type": "concept",
                "definition": sentence,
                "source_pages": chunk["pages"],
                "mastery": 0.0,
            })
    return concepts


def pdf_to_json(pdf_path, output_path="output/knowledge_output.json", max_chars=3000):
    """Extract a PDF into the JSON format consumed by generate_quiz_from_json."""
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pages = read_pdf(str(pdf_path))
    chunks = chunk_pages(pages, max_chars=max_chars)
    concepts = extract_concepts(chunks)
    result = {
        "status": "success",
        "document_path": str(pdf_path),
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "concepts": concepts,
        "relationships": [],
        "relations": [],
        "graph": {
            "nodes": [
                {
                    "id": concept["id"],
                    "name": concept["name"],
                    "type": concept["type"],
                    "source_pages": concept["source_pages"],
                }
                for concept in concepts
            ],
            "edges": [],
        },
        "chunks": chunks,
        "metadata": {
            "pipeline": "pdf -> pages -> chunks -> concepts -> quiz",
            "save_format": "json",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    pdf_to_json("data/slides/d1-slide-hackathon.pdf")
    print("Saved PDF knowledge JSON to output/knowledge_output.json")