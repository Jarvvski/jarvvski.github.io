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
- `hero` is an image file in the same folder. The page uses a full-height picture with the title on it. Zola makes the smaller sizes. Set `hero_alt`. `hero_credit` and `hero_credit_url` are the caption.
- A post with no `hero` gets a plain text header. The build draws a share image from the title.
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
