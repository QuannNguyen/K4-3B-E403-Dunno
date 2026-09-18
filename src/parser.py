from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import fitz


def read_pdf(pdf_path: str | Path) -> List[Dict[str, Any]]:
    """Read a PDF file and return page-by-page extracted text.

    Returns a list like:
        [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}]
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pages: List[Dict[str, Any]] = []
    document = fitz.open(str(pdf_path))
    try:
        for page_number in range(document.page_count):
            page = document[page_number]
            text = page.get_text("text", sort=True)
            pages.append({
                "page": page_number + 1,
                "text": text.strip(),
            })
    finally:
        document.close()

    return pages
