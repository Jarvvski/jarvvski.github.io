#!/usr/bin/env python3
import base64
import io
import json
import os
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageFilter

DEFAULT_MODEL = "@cf/black-forest-labs/flux-2-klein-9b"
GENERATED_NAME = "hero.webp"
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
MAX_EDGE = 2400
LQIP_EDGE = 24
HOUSE = (
    "A wide editorial photograph with natural light and a quiet palette. "
    "No text, no letters, no logos, no watermark, no real people, and no faces. "
    "Subject: {subject}"
)


class HeroError(Exception):
    pass


def model_id(root: Path, env: dict) -> str:
    chosen = env.get("CLOUDFLARE_AI_MODEL", "").strip()
    if chosen:
        return chosen
    path = root / "config.toml"
    if path.is_file():
        extra = tomllib.loads(path.read_text()).get("extra") or {}
        configured = extra.get("hero_model")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
    return DEFAULT_MODEL


def image_size(root: Path) -> tuple[int, int]:
    width = DEFAULT_WIDTH
    height = DEFAULT_HEIGHT
    path = root / "config.toml"
    if path.is_file():
        extra = tomllib.loads(path.read_text()).get("extra") or {}
        if "hero_width" in extra:
            width = extra["hero_width"]
        if "hero_height" in extra:
            height = extra["hero_height"]
    if isinstance(width, bool) or isinstance(height, bool) or not isinstance(width, int) or not isinstance(height, int):
        raise HeroError("hero_width and hero_height must be whole numbers")
    return width, height


def clean_model(model: str) -> str:
    if not model or any(char.isspace() for char in model) or ".." in model:
        raise HeroError(f"hero model id is not usable: {model}")
    return model


def prompt_for(title: str, description: str, hero_prompt: str) -> str:
    subject = hero_prompt.strip() or f"{title}. {description}".strip()
    subject = " ".join(subject.split())
    prefix = HOUSE.split("{subject}", 1)[0]
    room = 2048 - len(prefix)
    if len(subject) > room:
        subject = subject[:room].rstrip()
    return HOUSE.format(subject=subject)


def alt_text(title: str, description: str, hero_prompt: str) -> str:
    text = hero_prompt.strip() or f"{title}. {description}".strip()
    text = " ".join(text.split())
    if len(text) > 180:
        text = text[:180].rstrip()
    return text


def classify(extra: dict, folder: Path) -> str:
    if "hero" in extra:
        hero = extra.get("hero")
        if hero is False:
            return "none"
        if isinstance(hero, str) and hero.strip():
            return "manual"
        raise HeroError("hero must be a path or false")
    if (folder / GENERATED_NAME).is_file():
        return "generated"
    return "pending"


def posts(root: Path):
    folder = root / "content" / "posts"
    if not folder.is_dir():
        return
    for path in sorted(folder.rglob("*.md")):
        if path.name.startswith("_") or path.name != "index.md":
            continue
        text = path.read_text()
        if not text.startswith("+++"):
            continue
        _, front, _ = text.split("+++", 2)
        data = tomllib.loads(front)
        yield path, data


def toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if not isinstance(value, str):
        raise HeroError("front matter values must be text or booleans")
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def upsert_extra(text: str, values: dict) -> str:
    if not text.startswith("+++"):
        raise HeroError("missing front matter")
    end = text.find("+++", 3)
    if end < 0:
        raise HeroError("missing front matter close")
    lines = text[3:end].splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == "[extra]"), None)
    if start is None:
        block = ["", "[extra]"]
        block.extend(f"{key} = {toml_value(value)}" for key, value in values.items())
        lines.extend(block)
    else:
        stop = len(lines)
        for index in range(start + 1, len(lines)):
            stripped = lines[index].strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                stop = index
                break
        for key, value in values.items():
            rendered = f"{key} = {toml_value(value)}"
            found = None
            for index in range(start + 1, stop):
                piece = lines[index].strip()
                if piece.startswith(f"{key} ") or piece.startswith(f"{key}="):
                    found = index
                    break
            if found is None:
                lines.insert(start + 1, rendered)
                stop += 1
            else:
                lines[found] = rendered
    front = "\n".join(lines)
    if not front.endswith("\n"):
        front += "\n"
    return "+++" + front + text[end:]


def ensure_meta(path: Path, alt: str) -> bool:
    text = path.read_text()
    _, front, _ = text.split("+++", 2)
    extra = tomllib.loads(front).get("extra") or {}
    values = {}
    if extra.get("hero_generated") is not True:
        values["hero_generated"] = True
    if not (isinstance(extra.get("hero_alt"), str) and extra.get("hero_alt").strip()):
        values["hero_alt"] = alt
    if not values:
        return False
    path.write_text(upsert_extra(text, values))
    return True


def api_request(account: str, token: str, model: str, prompt: str, width: int, height: int):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"
    boundary = "----jarvisHero"
    fields = (
        ("prompt", prompt),
        ("width", str(width)),
        ("height", str(height)),
    )
    chunks = []
    for name, value in fields:
        chunks.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        )
    chunks.append(f"--{boundary}--\r\n")
    body = "".join(chunks).encode()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    return url, body, headers


def image_bytes(content_type: str, body: bytes) -> bytes:
    if content_type.lower().startswith("image/"):
        return body
    try:
        payload = json.loads(body.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HeroError("Workers AI returned a response that is not an image") from error
    if payload.get("success") is False:
        errors = payload.get("errors") or []
        message = errors[0].get("message") if errors and isinstance(errors[0], dict) else "request failed"
        raise HeroError(message)
    result = payload.get("result") if isinstance(payload.get("result"), dict) else payload
    encoded = result.get("image") if isinstance(result, dict) else None
    if not isinstance(encoded, str) or not encoded.strip():
        raise HeroError("Workers AI returned no image")
    try:
        return base64.b64decode(encoded)
    except ValueError as error:
        raise HeroError("Workers AI returned an image that is not base64") from error


def save_webp(raw: bytes, dest: Path) -> None:
    image = Image.open(io.BytesIO(raw))
    image.load()
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    image.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(".webp.tmp")
    image.save(temporary, "WEBP", quality=80, method=6)
    os.replace(temporary, dest)


def hero_source(extra: dict, folder: Path) -> Path | None:
    kind = classify(extra, folder)
    if kind == "manual":
        path = folder / str(extra.get("hero")).strip()
        return path if path.is_file() else None
    if kind == "generated":
        path = folder / GENERATED_NAME
        return path if path.is_file() else None
    return None


def lqip_data_uri(path: Path) -> str:
    image = Image.open(path)
    image.load()
    image = image.convert("RGB")
    image.thumbnail((LQIP_EDGE, LQIP_EDGE), Image.Resampling.LANCZOS)
    image = image.filter(ImageFilter.GaussianBlur(radius=1))
    buffer = io.BytesIO()
    image.save(buffer, "WEBP", quality=35, method=6)
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/webp;base64,{encoded}"


def write_placeholders(root: Path) -> Path:
    found = {}
    for path, data in posts(root):
        if data.get("draft") is True:
            continue
        source = hero_source(data.get("extra") or {}, path.parent)
        if source is None:
            continue
        found[path.relative_to(root / "content").as_posix()] = lqip_data_uri(source)
    dest = root / "data" / "hero_placeholders.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(found, indent=2, sort_keys=True) + "\n"
    if not dest.is_file() or dest.read_text() != payload:
        dest.write_text(payload)
    return dest


def default_fetch(url: str, body: bytes, headers: dict) -> tuple[int, str, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            content_type = response.headers.get("Content-Type", "")
            return response.status, content_type, response.read()
    except urllib.error.HTTPError as error:
        content_type = error.headers.get("Content-Type", "") if error.headers else ""
        return error.code, content_type, error.read()


def request_image(fetch, url: str, body: bytes, headers: dict, pause) -> tuple[int, str, bytes]:
    status, content_type, payload = 0, "", b""
    for attempt in range(3):
        status, content_type, payload = fetch(url, body, headers)
        if status < 500 or attempt == 2:
            return status, content_type, payload
        pause(2 * (attempt + 1))
    return status, content_type, payload


def generate(root: Path, env: dict, fetch, pause=None) -> int:
    if pause is None:
        pause = time.sleep
    account = env.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = env.get("CLOUDFLARE_AI_TOKEN", "").strip()
    if not account or not token:
        print("Hero generation skipped. CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_AI_TOKEN is unset.")
        return 0
    model = clean_model(model_id(root, env))
    width, height = image_size(root)
    wrote = 0
    for path, data in posts(root):
        if data.get("draft") is True:
            continue
        extra = data.get("extra") or {}
        kind = classify(extra, path.parent)
        title = str(data.get("title") or "")
        description = str(data.get("description") or "")
        hero_prompt = extra.get("hero_prompt") if isinstance(extra.get("hero_prompt"), str) else ""
        alt = alt_text(title, description, hero_prompt)
        if kind == "generated":
            if ensure_meta(path, alt):
                wrote += 1
            continue
        if kind != "pending":
            continue
        prompt = prompt_for(title, description, hero_prompt)
        url, body, headers = api_request(account, token, model, prompt, width, height)
        status, content_type, payload = request_image(fetch, url, body, headers, pause)
        if status >= 400:
            detail = payload[:300].decode(errors="replace").replace("\n", " ")
            raise HeroError(f"Workers AI returned {status} for {path.parent.name}: {detail}")
        raw = image_bytes(content_type, payload)
        save_webp(raw, path.parent / GENERATED_NAME)
        ensure_meta(path, alt)
        wrote += 1
        print(f"wrote {path.parent.relative_to(root) / GENERATED_NAME}")
    if wrote == 0:
        print("No new hero images.")
    return 0


def main(root: Path | None = None, env: dict | None = None, fetch=None, pause=None) -> int:
    try:
        site = root or Path(__file__).resolve().parents[1]
        code = generate(
            site,
            env if env is not None else dict(os.environ),
            fetch or default_fetch,
            pause,
        )
        write_placeholders(site)
        return code
    except HeroError as error:
        print(f"Hero generation failed. {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
