import re
from pathlib import Path

from workers.content_source import ContentSource, RawContent


class LocalFileSource(ContentSource):
    def supported_extensions(self) -> set[str]:
        return {".md", ".markdown", ".txt", ".pdf", ".docx"}

    def extract(self, path: str) -> RawContent | None:
        file_path = Path(path)
        if (
            file_path.suffix.lower() not in self.supported_extensions()
            or not file_path.exists()
        ):
            return None

        extension = file_path.suffix.lower()
        if extension in (".md", ".markdown"):
            return self._extract_markdown(file_path)
        if extension == ".txt":
            return self._extract_text(file_path)
        if extension == ".pdf":
            return self._extract_pdf(file_path)
        if extension == ".docx":
            return self._extract_docx(file_path)
        return None

    def _extract_markdown(self, path: Path) -> RawContent:
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("-", " ").replace("_", " ").title()
        match = re.match(r"^#\s+(.+)$", text, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            body = text[match.end() :].strip()
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

            document = pymupdf.open(str(path))
            text_parts = [page.get_text() for page in document]
            document.close()
            body = "\n\n".join(text_parts).strip()
            title = path.stem.replace("-", " ").replace("_", " ").title()
            if body:
                first_line = body.split("\n")[0].strip()
                if len(first_line) < 200:
                    title = first_line
            return RawContent(path=str(path), title=title, body=body)
        except ImportError:
            return RawContent(
                path=str(path), title=path.stem, body="[PDF extraction unavailable]"
            )

    def _extract_docx(self, path: Path) -> RawContent:
        try:
            from docx import Document

            document = Document(str(path))
            paragraphs = [
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]
            title = path.stem.replace("-", " ").replace("_", " ").title()
            if paragraphs:
                title = paragraphs[0]
                body = "\n\n".join(paragraphs[1:])
            else:
                body = ""
            return RawContent(path=str(path), title=title, body=body)
        except ImportError:
            return RawContent(
                path=str(path), title=path.stem, body="[DOCX extraction unavailable]"
            )
