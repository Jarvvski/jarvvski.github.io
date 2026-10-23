# jarvis.gg

Personal site and blog for Adam Jarvis. Zola builds the pages. GitHub Pages serves them at https://jarvis.gg.

## Write a post

Create a folder under `content/posts`. The folder name is the URL. `content/posts/my-note/index.md` is published at `/posts/my-note/`.

Put the front matter between `+++` lines.

```toml
+++
title = "My note"
description = "One sentence for the home page and for link previews."
date = 2026-10-23
updated = 2026-10-24
draft = false

[taxonomies]
tags = ["notes"]

[extra]
hero = "hero.jpg"
hero_alt = "What the picture shows"
hero_credit = "Name, license"
hero_credit_url = "https://example.com/the-picture"
toc = true
series = "Notes"
+++
```

Required fields are `title`, `date`, and `description`. The rest are optional.

- `updated` prints an updated date next to the published date.
- `draft = true` leaves the post out of the build. Preview it with `zola serve --drafts`.
- `hero` chooses the picture.
  - `hero = "hero.jpg"` uses that file. Set `hero_alt`. `hero_credit` and `hero_credit_url` are the caption.
  - Leave `hero` out and a `hero.webp` in the folder is used. The hero workflow can draw that file. See below.
  - `hero = false` keeps the text header. The build draws a share image from the title.
- `hero_prompt` is the subject for a generated picture. Without it, the generator uses the title and the description. One house style wraps every subject, so the pictures stay consistent, and it asks for no text and no real people.
- `hero_generated = true` marks a generated picture. The page prints "Generated image" under the title.
- `toc = true` lists the headings.
- `series` lists every post that uses the same name, oldest first.
- Tags go under `[taxonomies]`.

Footnotes use standard Markdown.

```markdown
A claim.[^1]

[^1]: The source.
```

Each heading gets an anchor.

The about page is `content/about.md`. To add a photo, move that file to `content/about/index.md`, put the image beside it, and set `photo` and `photo_alt` under `[extra]`.

```toml
[extra]
photo = "photo.jpg"
photo_alt = "Adam Jarvis"
```

Do not put an email address on the site.

## Generate a hero

The hero workflow runs on a pull request from this repository. It does not run for forks, and the Pages deploy does not call it.

Set `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_AI_TOKEN`, then from the repo root run:

```bash
python3 scripts/gen_heroes.py
```

If either variable is missing, the script prints a notice and exits 0. An existing `hero.webp` is left as it is. Delete that file to draw a new one.

The model id is `hero_model` in `config.toml`. The default is `@cf/black-forest-labs/flux-2-klein-9b`. The script sends `prompt`, `width`, and `height` as that model's REST API does, at 1024 pixels, then saves a webp no wider than 2400px. The model page is [flux-2-klein-9b](https://developers.cloudflare.com/workers-ai/models/flux-2-klein-9b/).

The repository secrets use those same two names.

## Preview locally

Install [Zola 0.23.6](https://github.com/getzola/zola/releases/tag/v0.23.6), then from the repo root run:

```bash
zola serve
```

Open the URL Zola prints. That is http://127.0.0.1:1111 by default.

Share images and search are part of the production build, not of `zola serve`. To preview those, install Python 3 with Pillow 11.3.0 and Node, then run:

```bash
python3 scripts/og_images.py
zola build --base-url http://127.0.0.1:8787
npx pagefind@1.5.2 --site public
python3 -m http.server -d public 8787
```

The `--base-url` flag keeps styles and scripts on the local host. A plain `zola build` points them at https://jarvis.gg, which is what the deploy uses.

## Deploy

Merging to `main` runs the Pages workflow. The workflow builds the site with Zola, indexes it with Pagefind, and deploys with GitHub Pages.

Before the first deploy, set the repository Pages source to GitHub Actions. Then set the custom domain to `jarvis.gg`. `static/CNAME` already contains that host.

Cloudflare Web Analytics stays off while `cloudflare_analytics_token` in `config.toml` is empty. Set the token under `[extra]` to include the snippet.

```toml
[extra]
cloudflare_analytics_token = ""
```
