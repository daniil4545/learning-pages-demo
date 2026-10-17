"""Build the static lecture catalog and validate local links, without network calls."""

import argparse
import html
import json
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"


class PageLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if value is None:
                continue
            if key == "id":
                self.ids.add(value)
            if key in {"href", "src", "poster"}:
                self.links.append(value)


def site_path(site: Path, name: str) -> Path:
    url = urlsplit(name)
    if url.scheme or url.netloc or url.query or url.fragment or name.startswith("/"):
        raise ValueError(f"Expected relative site path: {name}")
    target = (site / unquote(name)).resolve()
    if not target.is_relative_to(site.resolve()):
        raise ValueError(f"Path leaves the site: {name}")
    return target


def read_registry(root: Path, site: Path) -> list[dict]:
    entries = json.loads((root / "library.json").read_text())
    if not isinstance(entries, list):
        raise ValueError("library.json must be a list")
    seen = set()
    for entry in entries:
        validate_entry(entry)
        name = entry["path"]
        if not re.fullmatch(r"lectures/[a-z0-9][a-z0-9-]*\.html", name):
            raise ValueError(f"Invalid lecture path: {name}")
        if name in seen:
            raise ValueError(f"Duplicate lecture: {name}")
        seen.add(name)
        if not site_path(site, name).is_file():
            raise ValueError(f"Lecture not found: {name}")
        if "audio" in entry:
            validate_audio(site, entry["audio"])
    actual = {str(p.relative_to(site)) for p in site.rglob("*.html")}
    unlisted = actual - seen - {"index.html"}
    if unlisted:
        raise ValueError(f"Unlisted lecture pages: {sorted(unlisted)}")
    return entries


def validate_entry(entry: object) -> None:
    if not isinstance(entry, dict):
        raise ValueError("Each catalog entry must be an object")
    for key in ("path", "title", "description", "group"):
        if not isinstance(entry.get(key), str) or not entry[key].strip():
            raise ValueError(f"Missing catalog field: {key}")


def validate_audio(site: Path, audio: object) -> None:
    if not isinstance(audio, str) or not re.fullmatch(
        r"audio/[a-z0-9][a-z0-9-]*\.(mp3|m4a|ogg|wav)", audio
    ):
        raise ValueError(f"Invalid audio path: {audio}")
    if not site_path(site, audio).is_file():
        raise ValueError(f"Audio not found: {audio}")


def render_catalog(entries: list[dict]) -> str:
    groups = defaultdict(list)
    for entry in entries:
        groups[entry["group"]].append(entry)
    sections = []
    for number, (group, items) in enumerate(groups.items(), 1):
        cards = []
        for entry in items:
            audio = "Есть аудио" if entry.get("audio") else "Текст и схемы"
            cards.append(
                f'<a class="library-card" href="./{html.escape(entry["path"], quote=True)}">'
                f'<span class="library-meta">{audio}</span>'
                f"<h3>{html.escape(entry['title'])}</h3>"
                f"<p>{html.escape(entry['description'])}</p></a>"
            )
        sections.append(
            f'<section id="group-{number}"><h2>{html.escape(group)}</h2>'
            + "\n".join(cards)
            + "</section>"
        )
    return (
        """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark"><title>Библиотека лекций</title>
<link rel="stylesheet" href="./assets/library.css"></head>
<body class="library-index"><main class="library-catalog">
<header><p class="library-eyebrow">Учиться в своём темпе</p><h1>Библиотека лекций</h1>
<p class="library-lead">Объяснения, схемы и примеры по разработке.
Выбери тему и открой лекцию на любом устройстве.</p></header>
"""
        + "\n".join(sections)
        + "\n</main></body></html>\n"
    )


def render_lecture(text: str, entry: dict) -> str:
    # The shared template includes an example body tag inside a comment.
    text = re.sub(r"<!--(?:(?!-->).)*<body\b.*?-->", "", text, flags=re.S | re.I)
    # Some existing lectures rely on HTML's implicit body element.
    if not re.search(r"<body\b", text, flags=re.I):
        text, count = re.subn(r"(</(?:head|style)\s*>)", r"\1<body>", text, count=1, flags=re.I)
        if count != 1:
            raise ValueError(f"Missing page structure: {entry['path']}")
        text = re.sub(r"(?=</html\s*>)", "</body>", text, count=1, flags=re.I)
    for part in ("head", "body"):
        text = re.sub(
            rf"<!-- library-{part}:start -->.*?<!-- library-{part}:end -->\n?",
            "",
            text,
            flags=re.DOTALL,
        )
    styles = '<!-- library-head:start --><link rel="stylesheet" href="../assets/library.css">'
    styles += '<script defer src="../assets/player.js"></script><!-- library-head:end -->\n'
    if re.search(r"</head\s*>", text, flags=re.I):
        text = re.sub(r"(?=</head\s*>)", lambda _: styles, text, count=1, flags=re.I)
    else:
        text = re.sub(r"(?=<body[\s>])", lambda _: styles, text, count=1, flags=re.I)
    shell = '<!-- library-body:start --><div class="library-bar">'
    shell += '<a href="../index.html">Библиотека лекций</a>'
    shell += "<span>Текст и схемы</span></div>"
    if entry.get("audio"):
        shell += '<div class="library-player" role="region" aria-label="Аудиолекция">'
        shell += '<audio id="lecture-audio" controls preload="metadata" src="../'
        shell += html.escape(entry["audio"], quote=True) + '"></audio>'
        shell += (
            '<p id="audio-status" aria-live="polite">Позиция сохраняется в этом браузере.</p></div>'
        )
    shell += "<!-- library-body:end -->\n"
    text, count = re.subn(r"(<body\b[^>]*>)", lambda m: m[1] + shell, text, count=1, flags=re.I)
    if count != 1:
        raise ValueError(f"Missing body element: {entry['path']}")
    return text


def check_links(site: Path, pages: dict[Path, str]) -> list[str]:
    parsed = {}
    errors = []
    for path, text in pages.items():
        parser = PageLinks()
        parser.feed(text)
        parsed[path.resolve()] = parser
    for path, parser in parsed.items():
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme in {"https", "http", "mailto", "tel", "data"} or url.netloc:
                continue
            if url.scheme or url.path.startswith("/"):
                errors.append(f"{path.name}: nonportable link {link}")
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.is_relative_to(site.resolve()) or (
                target not in parsed and not target.is_file()
            ):
                errors.append(f"{path.name}: missing local target {link}")
            elif (
                url.fragment
                and target in parsed
                and unquote(url.fragment) not in parsed[target].ids
            ):
                errors.append(f"{path.name}: missing anchor {link}")
    return errors


def prepare(root: Path, site: Path) -> dict[Path, str]:
    entries = read_registry(root, site)
    pages = {site / "index.html": render_catalog(entries)}
    for entry in entries:
        path = site_path(site, entry["path"])
        pages[path] = render_lecture(path.read_text(), entry)
    return pages


def run(root: Path, site: Path, check: bool) -> None:
    pages = prepare(root, site)
    # Validate the complete prospective output before changing any page.
    errors = check_links(site, pages)
    if errors:
        raise ValueError("\n".join(errors))
    for path, content in pages.items():
        if check:
            if not path.is_file() or path.read_text() != content:
                raise ValueError(f"Generated page is stale; run build: {path.name}")
        else:
            path.write_text(content)
    print(f"PASS: {len(pages) - 1} lectures, catalog and local links")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args()
    try:
        run(ROOT, SITE, check=args.command == "check")
    except (ValueError, OSError) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
