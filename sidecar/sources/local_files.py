import re
from pathlib import Path
from sources.base import ContentSource, RawContent


class LocalFileSource(ContentSource):
    def supported_extensions(self) -> set[str]:
        return {".md", ".markdown", ".txt", ".pdf", ".docx"}

    def extract(self, path: str) -> RawContent | None:
        p = Path(path)
        if p.suffix.lower() not in self.supported_extensions():
            return None
        if not p.exists():
            return None
        ext = p.suffix.lower()
        if ext in (".md", ".markdown"):
            return self._extract_markdown(p)
        elif ext == ".txt":
            return self._extract_text(p)
        elif ext == ".pdf":
            return self._extract_pdf(p)
        elif ext == ".docx":
            return self._extract_docx(p)
        return None

    def _extract_markdown(self, path: Path) -> RawContent:
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("-", " ").replace("_", " ").title()
        match = re.match(r"^#\s+(.+)$", text, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            body = text[match.end():].strip()
        else:
            body = text.strip()
        return RawContent(path=str(path), title=title, body=body)

    def _extract_text(self, path: Path) -> RawContent:
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("-", " ").replace("_", " ").title()
        return RawContent(path=str(path), title=title, body=text.strip())

    def _extract_pdf(self, path: Path) -> RawContent:
        try:
            import pymupdf
            doc = pymupdf.open(str(path))
            text_parts = [page.get_text() for page in doc]
            doc.close()
            body = "\n\n".join(text_parts).strip()
            title = path.stem.replace("-", " ").replace("_", " ").title()
            if body:
                first_line = body.split("\n")[0].strip()
                if len(first_line) < 200:
                    title = first_line
            return RawContent(path=str(path), title=title, body=body)
        except ImportError:
            return RawContent(path=str(path), title=path.stem, body="[PDF extraction unavailable]")

    def _extract_docx(self, path: Path) -> RawContent:
        try:
            from docx import Document
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            title = path.stem.replace("-", " ").replace("_", " ").title()
            if paragraphs:
                title = paragraphs[0]
                body = "\n\n".join(paragraphs[1:])
            else:
                body = ""
            return RawContent(path=str(path), title=title, body=body)
        except ImportError:
            return RawContent(path=str(path), title=path.stem, body="[DOCX extraction unavailable]")
