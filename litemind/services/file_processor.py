import io
import csv
import json
from typing import Dict, Any, Optional
import pypdf
import docx
from PIL import Image


class FileProcessor:
    """
    Parses uploaded user files (PDF, DOCX, TXT, CSV, images) and extracts clean text context
    to pass as untrusted context into LiteMind workflow DAG tasks.
    """

    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB limit

    @classmethod
    def extract_text_from_file(cls, filename: str, content_bytes: bytes) -> Dict[str, Any]:
        """
        Extract structured text and metadata safely from uploaded file bytes.
        """
        if len(content_bytes) > cls.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum allowed size of 25MB.")

        ext = filename.lower().split(".")[-1] if "." in filename else ""

        extracted_text = ""
        file_type = ext

        try:
            if ext == "pdf":
                reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                pages_text = []
                for idx, page in enumerate(reader.pages[:50]):  # Cap at 50 pages
                    t = page.extract_text()
                    if t:
                        pages_text.append(f"--- Page {idx+1} ---\n{t.strip()}")
                extracted_text = "\n\n".join(pages_text)
                file_type = "PDF Document"

            elif ext in ("docx", "doc"):
                doc = docx.Document(io.BytesIO(content_bytes))
                paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                extracted_text = "\n".join(paragraphs)
                file_type = "Word Document"

            elif ext in ("txt", "md", "json"):
                extracted_text = content_bytes.decode("utf-8", errors="ignore")
                file_type = "Text File"

            elif ext == "csv":
                text_stream = io.StringIO(content_bytes.decode("utf-8", errors="ignore"))
                reader = csv.reader(text_stream)
                rows = [", ".join(row) for row in list(reader)[:100]]  # Cap at 100 rows
                extracted_text = "\n".join(rows)
                file_type = "CSV Data"

            elif ext in ("jpg", "jpeg", "png", "webp"):
                img = Image.open(io.BytesIO(content_bytes))
                extracted_text = f"Image metadata: Format={img.format}, Size={img.size}, Mode={img.mode}."
                file_type = "Image File"

            else:
                extracted_text = content_bytes.decode("utf-8", errors="ignore")[:5000]
                file_type = "Raw File"

        except Exception as e:
            extracted_text = f"Could not parse file content: {str(e)}"

        return {
            "filename": filename,
            "file_type": file_type,
            "size_bytes": len(content_bytes),
            "extracted_text": extracted_text[:20000]  # Cap context length for LLM safety
        }
