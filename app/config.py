import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_UNSAFE_STEM = re.compile(r"[^\w.\- ()]+")


def load_dotenv(path: Path) -> None:
    """Load KEY=VALUE lines when the process has not already exported them."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def document_stem(filename: str | None) -> str:
    """Turn an uploaded filename into a single safe path segment."""
    raw_name = Path(filename or "document.pdf").name
    stem = _UNSAFE_STEM.sub("_", Path(raw_name).stem).strip(" ._")
    if not stem:
        return "document"
    return stem[:180]


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_base_url: str
    groq_model: str
    render_scale: float
    root: Path
    raw_pdfs: Path
    json_dir: Path
    markdown_dir: Path
    processed_pdf_dir: Path
    crops_dir: Path

    def ensure_dirs(self) -> None:
        for directory in (
            self.raw_pdfs,
            self.json_dir,
            self.markdown_dir,
            self.processed_pdf_dir,
            self.crops_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    return Settings(
        groq_api_key=os.environ.get("GROQ_API_KEY", ""),
        groq_base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        groq_model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"),
        render_scale=float(os.environ.get("RENDER_SCALE", "2.0")),
        root=ROOT,
        raw_pdfs=ROOT / "raw_pdfs",
        json_dir=ROOT / "json",
        markdown_dir=ROOT / "markdown",
        processed_pdf_dir=ROOT / "processed_pdf",
        crops_dir=ROOT / "storage" / "crops",
    )
