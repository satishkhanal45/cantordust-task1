import fitz  
from pathlib import Path


def extract_text(pdf_path: str | Path) -> str:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(path))
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if text.strip():
            pages.append(f"--- Page {i} ---\n{text.strip()}")
    doc.close()

    return "\n\n".join(pages)


def extract_all(data_dir: str | Path) -> dict[str, str]:
    data_dir = Path(data_dir)
    results = {}
    for pdf_file in sorted(data_dir.glob("*.pdf")):
        results[pdf_file.name] = extract_text(pdf_file)
    return results
