#!/usr/bin/env python3
import base64
import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import gen_heroes


def jpeg_payload() -> bytes:
    image = Image.new("RGB", (64, 36), (30, 60, 90))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return json.dumps({"success": True, "result": {"image": encoded}}).encode()


def write_post(folder: Path, extra: str, draft: bool = False) -> None:
    folder.mkdir(parents=True)
    draft_line = "draft = true\n" if draft else ""
    folder.joinpath("index.md").write_text(
        "+++\n"
        'title = "Desk"\n'
        'description = "Morning light on an empty desk."\n'
        "date = 2026-10-21\n"
        f"{draft_line}"
        "[extra]\n"
        f"{extra}"
        "+++\n\n"
        "Body.\n"
    )


class HeroesTest(unittest.TestCase):
    def test_prompt_uses_the_house_style_and_the_author_subject(self):
        prompt = gen_heroes.prompt_for("Desk", "Morning light.", "an empty chair by a window")
        self.assertIn("No text", prompt)
        self.assertIn("no real people", prompt)
        self.assertIn("an empty chair by a window", prompt)
        self.assertNotIn("Morning light.", prompt)

    def test_prompt_falls_back_to_the_title_and_description(self):
        prompt = gen_heroes.prompt_for("Desk", "Morning light.", "")
        self.assertIn("Desk. Morning light.", prompt)
        self.assertLessEqual(len(prompt), 2048)

    def test_alt_text_is_the_subject_not_the_house_style(self):
        alt = gen_heroes.alt_text("Desk", "Morning light.", "an empty chair")
        self.assertEqual(alt, "an empty chair")
        self.assertNotIn("no real people", alt)

    def test_precedence_and_idempotent_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manual = root / "content" / "posts" / "manual"
            blocked = root / "content" / "posts" / "blocked"
            open_post = root / "content" / "posts" / "open"
            draft = root / "content" / "posts" / "draft"
            write_post(manual, 'hero = "hero.jpg"\n')
            write_post(blocked, "hero = false\n")
            write_post(open_post, 'hero_prompt = "an empty chair by a window"\n')
            write_post(draft, 'hero_prompt = "a closed door"\n', draft=True)
            calls = []

            def fetch(url, body, headers):
                calls.append((url, body, headers))
                return 200, "application/json", jpeg_payload()

            env = {
                "CLOUDFLARE_ACCOUNT_ID": "account",
                "CLOUDFLARE_AI_TOKEN": "token",
                "CLOUDFLARE_AI_MODEL": "@cf/black-forest-labs/flux-2-klein-9b",
            }
            self.assertEqual(gen_heroes.main(root, env, fetch), 0)
            self.assertEqual(len(calls), 1)
            url, body, headers = calls[0]
            self.assertTrue(url.endswith("/accounts/account/ai/run/@cf/black-forest-labs/flux-2-klein-9b"))
            self.assertIn(b"an empty chair by a window", body)
            self.assertIn(b'name="width"', body)
            self.assertIn(b'name="height"', body)
            self.assertIn(b"\r\n1920\r\n", body)
            self.assertIn(b"\r\n1080\r\n", body)
            self.assertTrue(headers["Authorization"].startswith("Bearer "))
            image = open_post / "hero.webp"
            self.assertTrue(image.is_file())
            with Image.open(image) as saved:
                self.assertEqual(saved.format, "WEBP")
                self.assertLessEqual(saved.size[0], 2400)
            text = (open_post / "index.md").read_text()
            self.assertIn("hero_generated = true", text)
            self.assertIn('hero_alt = "an empty chair by a window"', text)
            self.assertNotIn('hero = "hero.webp"', text)
            self.assertFalse((manual / "hero.webp").exists())
            self.assertFalse((blocked / "hero.webp").exists())
            self.assertFalse((draft / "hero.webp").exists())

            self.assertEqual(gen_heroes.main(root, env, fetch), 0)
            self.assertEqual(len(calls), 1)

            image.unlink()
            self.assertEqual(gen_heroes.main(root, env, fetch), 0)
            self.assertEqual(len(calls), 2)
            self.assertTrue(image.is_file())

    def test_size_comes_from_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config.toml").write_text("[extra]\nhero_width = 1280\nhero_height = 720\n")
            write_post(root / "content" / "posts" / "open", "")
            calls = []

            def fetch(url, body, headers):
                calls.append(body)
                return 200, "application/json", jpeg_payload()

            env = {"CLOUDFLARE_ACCOUNT_ID": "account", "CLOUDFLARE_AI_TOKEN": "token"}
            self.assertEqual(gen_heroes.main(root, env, fetch), 0)
            self.assertIn(b"\r\n1280\r\n", calls[0])
            self.assertIn(b"\r\n720\r\n", calls[0])
            self.assertNotIn(b"\r\n1920\r\n", calls[0])

    def test_workers_ai_500_is_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_post(root / "content" / "posts" / "open", 'hero_prompt = "a closed notebook"\n')
            calls = []

            def fetch(url, body, headers):
                calls.append(url)
                if len(calls) == 1:
                    return 500, "application/json", b'{"success":false}'
                return 200, "application/json", jpeg_payload()

            env = {"CLOUDFLARE_ACCOUNT_ID": "account", "CLOUDFLARE_AI_TOKEN": "token"}
            self.assertEqual(gen_heroes.main(root, env, fetch, pause=lambda _seconds: None), 0)
            self.assertEqual(len(calls), 2)
            self.assertTrue((root / "content" / "posts" / "open" / "hero.webp").is_file())

    def test_missing_secret_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_post(root / "content" / "posts" / "open", "")
            calls = []
            code = gen_heroes.main(root, {}, lambda *args: calls.append(args))
            self.assertEqual(code, 0)
            self.assertEqual(calls, [])
            self.assertFalse((root / "content" / "posts" / "open" / "hero.webp").exists())

    def test_placeholder_is_a_tiny_inline_webp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manual = root / "content" / "posts" / "manual"
            blocked = root / "content" / "posts" / "blocked"
            write_post(manual, 'hero = "hero.jpg"\n')
            write_post(blocked, "hero = false\n")
            image = Image.new("RGB", (400, 200), (20, 90, 140))
            image.save(manual / "hero.jpg", format="JPEG")
            dest = gen_heroes.write_placeholders(root)
            found = json.loads(dest.read_text())
            self.assertEqual(list(found), ["posts/manual/index.md"])
            uri = found["posts/manual/index.md"]
            self.assertTrue(uri.startswith("data:image/webp;base64,"))
            raw = base64.b64decode(uri.split(",", 1)[1])
            with Image.open(io.BytesIO(raw)) as preview:
                self.assertEqual(preview.format, "WEBP")
                self.assertGreaterEqual(preview.size[0], 16)
                self.assertLessEqual(preview.size[0], 32)

    def test_published_post_waits_for_a_generated_hero(self):
        root = Path(__file__).resolve().parents[1]
        found = {}
        for path, data in gen_heroes.posts(root):
            found[path.parent.name] = (
                data.get("draft") is True,
                gen_heroes.classify(data.get("extra") or {}, path.parent),
            )
        self.assertEqual(set(found), {"why-a-blog-why-now"})
        draft, kind = found["why-a-blog-why-now"]
        self.assertFalse(draft)
        self.assertIn(kind, {"pending", "generated"})


if __name__ == "__main__":
    unittest.main()
