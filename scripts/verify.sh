#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
public="$root/public"
fail() { echo "verify: $1" >&2; exit 1; }

test -f "$public/index.html"
test -f "$public/about/index.html"
test -f "$public/search/index.html"
test -f "$public/posts/a-place-for-notes/index.html"
test -f "$public/posts/a-second-note/index.html"
test -f "$public/404.html"
test -f "$public/sitemap.xml"
test -f "$public/robots.txt"
test -f "$public/atom.xml"
test -f "$public/rss.xml"
test -f "$public/CNAME"
test -f "$public/giallo-light.css"
test -f "$public/giallo-dark.css"
test -f "$public/style.css"
test -f "$public/og/default.png"
test -f "$public/og/a-second-note.png"
test -f "$public/pagefind/pagefind.js"
test -f "$public/pagefind/pagefind-ui.js"

if find "$public" -iname '*unpublished*' | grep -q .; then
  fail "draft was published"
fi
if grep -R -n "Not yet" "$public" --include='*.html' --include='*.xml' >/dev/null; then
  fail "draft title is in the output"
fi

hero="$public/posts/a-place-for-notes/index.html"
second="$public/posts/a-second-note/index.html"
about="$public/about/index.html"
home="$public/index.html"
search="$public/search/index.html"

grep -q 'class="hero"' "$hero"
grep -q 'srcset=' "$hero"
grep -q 'data-lang="rust"' "$hero"
grep -q 'data-lang="kotlin"' "$hero"
grep -q 'data-lang="go"' "$hero"
grep -q 'data-lang="mermaid"' "$hero"
grep -q 'class="footnotes"' "$hero"
grep -q 'class="toc"' "$hero"
grep -q 'class="series"' "$hero"
grep -q 'a-second-note' "$hero"
grep -q 'property="og:image"' "$hero"
grep -q 'twitter:card' "$hero"
grep -q 'application/ld+json' "$hero"
grep -q '"@type": "Article"' "$hero" || grep -q '"@type":"Article"' "$hero"
grep -q 'js/mermaid.js' "$hero"
grep -q 'localStorage.getItem("theme")' "$hero"
grep -q 'id="theme-toggle"' "$hero"
grep -q 'id="hl-light"' "$hero"
grep -q 'id="hl-dark"' "$hero"

grep -q 'Updated' "$second"
grep -q 'a-place-for-notes' "$second"
grep -q 'og/a-second-note.png' "$second"
if grep -q 'class="hero"' "$second"; then
  fail "text post rendered a hero"
fi
if grep -q 'class="toc"' "$second"; then
  fail "toc rendered without the flag"
fi
if grep -q 'mermaid.js' "$second"; then
  fail "mermaid loaded on a page without a diagram"
fi

grep -q 'github.com/Jarvvski' "$about"
grep -q 'x.com/__adamjarvis' "$about"
grep -q '"@type": "Person"' "$about" || grep -q '"@type":"Person"' "$about"
grep -q 'post-list' "$home"
grep -q 'min read' "$home"
grep -q 'pagefind-ui.js' "$search"
grep -q 'jarvis.gg' "$public/CNAME"
grep -q 'Sitemap: https://jarvis.gg/sitemap.xml' "$public/robots.txt"
grep -q 'prefers-reduced-motion' "$public/style.css"
grep -q 'Source Serif 4' "$public/style.css"
if grep -q 'fonts.googleapis.com' "$public/style.css"; then
  fail "stylesheet requests Google Fonts"
fi

if grep -R -n -E 'mailto:|available for hire|open to work' "$public" --include='*.html' --include='*.xml' --include='*.txt' >/dev/null; then
  fail "forbidden phrase in the built site"
fi
if grep -R -n 'cloudflareinsights' "$public" --include='*.html' >/dev/null; then
  fail "analytics snippet rendered with an empty token"
fi

echo "verify: ok"
