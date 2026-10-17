import json
import tempfile
import unittest
from pathlib import Path

import library


class LibraryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site = self.root / "site"
        (self.site / "lectures").mkdir(parents=True)
        (self.site / "assets").mkdir()
        (self.site / "assets/library.css").touch()
        (self.site / "assets/player.js").touch()
        self.page = self.site / "lectures/example.html"
        self.page.write_text('<html><body><h1 id="idea">Example</h1></body></html>')
        self.entry = {
            "path": "lectures/example.html",
            "title": "Example",
            "description": "Example lesson",
            "group": "Topics",
        }
        self.write_registry([self.entry])

    def write_registry(self, entries: list[dict]) -> None:
        (self.root / "library.json").write_text(json.dumps(entries))

    def test_build_is_repeatable_without_audio(self) -> None:
        library.run(self.root, self.site, check=False)
        first = self.page.read_text()
        library.run(self.root, self.site, check=False)
        self.assertEqual(first, self.page.read_text())
        self.assertNotIn("<audio", first)
        self.assertEqual(first.count('class="library-bar"'), 1)
        library.run(self.root, self.site, check=True)

    def test_implicit_body_from_existing_template(self) -> None:
        self.page.write_text("<html><style>body{margin:0}</style><main>Lesson</main></html>")
        library.run(self.root, self.site, check=False)
        library.run(self.root, self.site, check=True)
        self.assertEqual(self.page.read_text().count('class="library-bar"'), 1)

    def test_body_example_inside_template_comment(self) -> None:
        self.page.write_text(
            '<!doctype html><!-- Example: <body class="deck"> -->'
            "<html><head><title>Lesson</title></head>"
            "<body><main>Example</main></body></html>"
        )
        library.run(self.root, self.site, check=False)
        text = self.page.read_text()
        self.assertIn("<body><!-- library-body:start -->", text)
        library.run(self.root, self.site, check=True)

    def test_missing_lecture_fails(self) -> None:
        self.page.unlink()
        with self.assertRaisesRegex(ValueError, "Lecture not found"):
            library.prepare(self.root, self.site)

    def test_missing_local_anchor_prevents_writes(self) -> None:
        text = '<html><body><a href="#missing">Broken</a></body></html>'
        self.page.write_text(text)
        with self.assertRaisesRegex(ValueError, "missing anchor"):
            library.run(self.root, self.site, check=False)
        self.assertEqual(self.page.read_text(), text)

    def test_local_reference_cannot_escape_site(self) -> None:
        self.page.write_text('<html><body><a href="../../secret.txt">Bad</a></body></html>')
        (self.root / "secret.txt").write_text("not public")
        with self.assertRaisesRegex(ValueError, "missing local target"):
            library.run(self.root, self.site, check=False)

    def test_audio_must_exist_before_adding_player(self) -> None:
        self.entry["audio"] = "audio/example.mp3"
        self.write_registry([self.entry])
        with self.assertRaisesRegex(ValueError, "Audio not found"):
            library.prepare(self.root, self.site)
        (self.site / "audio").mkdir()
        (self.site / "audio/example.mp3").touch()
        library.run(self.root, self.site, check=False)
        self.assertIn('<audio id="lecture-audio" controls', self.page.read_text())
        self.assertNotIn("<select", self.page.read_text())

    def test_unlisted_html_does_not_publish_silently(self) -> None:
        (self.site / "lectures/report.html").write_text("<html><body>Report</body></html>")
        with self.assertRaisesRegex(ValueError, "Unlisted lecture"):
            library.prepare(self.root, self.site)

    def test_unlisted_html_anywhere_in_site_is_rejected(self) -> None:
        for relative in ("report.html", "lectures/drafts/report.html"):
            with self.subTest(path=relative):
                extra = self.site / relative
                extra.parent.mkdir(parents=True, exist_ok=True)
                extra.write_text("<html><body>Private report</body></html>")
                with self.assertRaisesRegex(ValueError, "Unlisted lecture"):
                    library.prepare(self.root, self.site)
                extra.unlink()

    def test_registry_rejects_traversal(self) -> None:
        self.entry["path"] = "../secret.html"
        self.write_registry([self.entry])
        with self.assertRaisesRegex(ValueError, "Invalid lecture path"):
            library.prepare(self.root, self.site)


if __name__ == "__main__":
    unittest.main()
