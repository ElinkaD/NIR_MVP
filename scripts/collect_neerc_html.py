"""Collect a small NEERC wiki HTML subset for the ETL pilot dataset."""

from __future__ import annotations

import argparse
import csv
import html as html_lib
import re
import time
from pathlib import Path
from urllib.parse import quote, urldefrag, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

START_URL = "https://neerc.ifmo.ru/wiki/index.php?title=Заглавная_страница"
MANIFEST_FIELDS = [
    "file_id",
    "file_name",
    "relative_path",
    "format",
    "source_type",
    "source_url",
    "topic_expected",
    "difficulty_expected",
    "has_text_layer",
    "is_duplicate",
    "is_bad_file",
    "comment",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download educational HTML pages from NEERC wiki.")
    parser.add_argument("--start-url", default=START_URL, help="Start page for link discovery.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of pages to save.")
    parser.add_argument("--output", default="data/real_input/html", help="Output directory for HTML files.")
    parser.add_argument("--manifest", default="datasets/manifest.csv", help="Dataset manifest path.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds.")
    return parser.parse_args()


def fetch_text(url: str) -> str:
    request = Request(iri_to_uri(url), headers={"User-Agent": "NIR-MVP-pilot-dataset/1.0"})
    with urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="ignore")


def iri_to_uri(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc.encode("idna").decode("ascii"),
            quote(parsed.path),
            parsed.params,
            quote(parsed.query, safe="%=&?/:"),
            quote(parsed.fragment),
        )
    )


def extract_wiki_links(html: str, base_url: str) -> list[str]:
    links = re.findall(r'href=["\']([^"\']+)["\']', html)
    result: list[str] = []
    seen: set[str] = set()
    for link in links:
        clean_link = html_lib.unescape(link)
        absolute, _fragment = urldefrag(urljoin(base_url, clean_link))
        parsed = urlparse(absolute)
        if parsed.netloc != "neerc.ifmo.ru":
            continue
        if "/wiki/index.php" not in parsed.path:
            continue
        if any(
            marker in absolute
            for marker in ("action=", "oldid=", "printable=", "feed=", "Special:", "Служебная:")
        ):
            continue
        if absolute not in seen:
            seen.add(absolute)
            result.append(absolute)
    return result


def slugify(value: str, fallback: str) -> str:
    value = re.sub(r"^.*title=", "", value)
    value = re.sub(r"[^\wа-яА-ЯёЁ-]+", "_", value, flags=re.UNICODE).strip("_")
    return (value[:80] or fallback).lower()


def read_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def upsert_manifest_rows(manifest_path: Path, new_rows: list[dict[str, str]]) -> None:
    rows = read_manifest(manifest_path)
    by_path = {row["relative_path"]: row for row in rows if row.get("relative_path")}
    for row in new_rows:
        by_path[row["relative_path"]] = row
    write_manifest(manifest_path, list(by_path.values()))


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    print(f"Fetching start page: {args.start_url}")
    start_html = fetch_text(args.start_url)
    links = extract_wiki_links(start_html, args.start_url)
    print(f"Discovered candidate links: {len(links)}")

    manifest_rows: list[dict[str, str]] = []
    saved = 0
    for index, url in enumerate(links, start=1):
        if saved >= args.limit:
            break
        try:
            time.sleep(args.delay)
            html = fetch_text(url)
            file_name = f"neerc_{saved + 1:03d}_{slugify(url, str(index))}.html"
            output_path = output / file_name
            output_path.write_text(html, encoding="utf-8")
            manifest_rows.append(
                {
                    "file_id": f"html_neerc_{saved + 1:03d}",
                    "file_name": file_name,
                    "relative_path": str(output_path.as_posix()),
                    "format": "html",
                    "source_type": "neerc_wiki",
                    "source_url": url,
                    "topic_expected": "programming/mathematics",
                    "difficulty_expected": "unknown",
                    "has_text_layer": "true",
                    "is_duplicate": "false",
                    "is_bad_file": "false",
                    "comment": "Downloaded from NEERC wiki for pilot ETL testing.",
                }
            )
            saved += 1
            print(f"[saved] {file_name}")
        except Exception as exc:
            print(f"[error] {url}: {exc}")

    upsert_manifest_rows(Path(args.manifest), manifest_rows)
    print(f"Saved pages: {saved}")
    print(f"Manifest updated: {args.manifest}")


if __name__ == "__main__":
    main()
