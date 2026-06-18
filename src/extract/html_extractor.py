"""HTML extraction adapter based on BeautifulSoup."""

from __future__ import annotations

from pathlib import Path

from .base import ExtractionResult


class HtmlExtractor:
    def extract(self, path: Path) -> ExtractionResult:
        try:
            from bs4 import BeautifulSoup, FeatureNotFound
        except Exception as exc:  # pragma: no cover - depends on optional package state
            return ExtractionResult(
                extraction_status="failed",
                errors=[f"BeautifulSoup import failed: {exc}"],
            )

        try:
            raw_html = path.read_text(encoding="utf-8", errors="ignore")
            try:
                soup = BeautifulSoup(raw_html, "lxml")
            except FeatureNotFound:
                soup = BeautifulSoup(raw_html, "html.parser")

            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()

            title = soup.title.get_text(" ", strip=True) if soup.title else None
            headings = [
                heading.get_text(" ", strip=True)
                for heading in soup.find_all(["h1", "h2", "h3"])
                if heading.get_text(" ", strip=True)
            ]
            meta_tags = {}
            for meta in soup.find_all("meta"):
                key = meta.get("name") or meta.get("property")
                value = meta.get("content")
                if key and value:
                    meta_tags[str(key)] = str(value)
            text = soup.get_text("\n", strip=True)
            return ExtractionResult(
                text=text,
                page_count=None,
                title=title,
                author=None,
                headings=headings,
                metadata={"title": title, "headings": headings, "meta": meta_tags},
                extractor_used="BeautifulSoup",
                extractor_status="success" if text.strip() else "failed",
                extraction_status="success" if text.strip() else "failed",
                errors=[] if text.strip() else ["HTML visible text is empty"],
            )
        except Exception as exc:
            return ExtractionResult(
                extractor_used="BeautifulSoup",
                extractor_status="failed",
                extraction_status="failed",
                errors=[f"HTML extraction failed: {exc}"],
            )
