#!/usr/bin/env bash
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
public="$root/public"
fail() { echo "verify: $1" >&2; exit 1; }

test -f "$public/index.html"
test -f "$public/about/index.html"
test -f "$public/search/index.html"
test -f "$public/posts/why-a-blog-why-now/index.html"
test -f "$public/404.html"
test -f "$public/sitemap.xml"
test -f "$public/robots.txt"
test -f "$public/atom.xml"
test -f "$public/rss.xml"
test -f "$public/CNAME"
test -f "$public/giallo.css"
if test -f "$public/giallo-light.css" || test -f "$public/giallo-dark.css"; then
  fail "syntax highlighting still ships a light or dual theme"
fi
test -f "$public/style.css"
test -f "$public/og/default.png"
test -f "$public/pagefind/pagefind.js"
test -f "$public/pagefind/pagefind-ui.js"

if find "$public" -iname '*unpublished*' | grep -q .; then
  fail "draft was published"
fi
if grep -R -n "Not yet" "$public" --include='*.html' --include='*.xml' >/dev/null; then
  fail "draft title is in the output"
fi
for sample in a-place-for-notes a-second-note an-open-picture; do
  if find "$public" -iname "*${sample}*" | grep -q .; then
    fail "sample post remains: $sample"
  fi
done
if grep -R -n -E 'A place for notes|A second note|An open picture' "$public" --include='*.html' --include='*.xml' >/dev/null; then
  fail "sample post title remains in the output"
fi

post="$public/posts/why-a-blog-why-now/index.html"
about="$public/about/index.html"
home="$public/index.html"
search="$public/search/index.html"

grep -q 'Why a blog, why now' "$post"
grep -q 'Writing clearly is the work, and a public place to practice.' "$post"
grep -q 'https://github.com/Jarvvski/jjfx' "$post"
grep -q 'October 24, 2026' "$post"
grep -q 'tags/writing/' "$post"
grep -q 'tags/agents/' "$post"
# Date, reading time, and tag pills share one meta row, ahead of the title.
if ! awk '
  /class="meta"/ { grab = 1; buf = "" }
  grab { buf = buf $0 "\n" }
  grab && /<\/div>/ {
    if (buf ~ /class="meta-line"/ && buf ~ /class="tags"/ && buf ~ /min read/ && buf ~ /tags\/writing\//) ok = 1
    exit
  }
  END { exit !ok }
' "$post"; then
  fail "post tags are not on the meta row"
fi
grep -q 'property="og:image"' "$post"
grep -q 'twitter:card' "$post"
grep -q 'application/ld+json' "$post"
grep -q '"@type": "Article"' "$post" || grep -q '"@type":"Article"' "$post"
grep -q 'giallo.css' "$post"
grep -q 'name="color-scheme" content="dark"' "$post"
grep -q 'why-a-blog-why-now' "$public/atom.xml"
grep -q 'why-a-blog-why-now' "$public/sitemap.xml"
if grep -q 'theme-toggle\|giallo-light\|localStorage\|prefers-color-scheme' "$post"; then
  fail "light theme switch remains in the page"
fi
if grep -q 'prefers-color-scheme' "$public/style.css"; then
  fail "stylesheet still switches on color scheme"
fi
if grep -q 'lightVars' "$public/js/mermaid.js"; then
  fail "mermaid still has a light theme"
fi
if grep -q 'setItem("theme"\|getItem("theme"' "$public/js/site.js"; then
  fail "site script still stores a theme"
fi
if grep -q 'class="toc"' "$post"; then
  fail "toc rendered without the flag"
fi
if grep -q 'class="series"' "$post"; then
  fail "series rendered without the field"
fi
if grep -q 'mermaid.js' "$post"; then
  fail "mermaid loaded on a page without a diagram"
fi
if grep -q 'hero-blur' "$post" || grep -q 'hero-blur' "$public/style.css"; then
  fail "hero blur remains"
fi
if grep -q 'hero-shade' "$post" || grep -q 'hero-shade' "$public/style.css"; then
  fail "hero shade remains"
fi

# The hero file arrives from the heroes workflow. Until then the post is a text page
# with a drawn share image. After hero.webp lands, the picture replaces that card.
if grep -q 'class="hero"' "$post"; then
  grep -q 'class="hero-fade"' "$post"
  grep -q 'Generated image' "$post"
  grep -q 'alt="an open notebook beside a closed laptop on a dark wooden desk at blue hour, soft window light, cool charcoal palette, shallow depth of field, quiet cinematic still"' "$post"
  grep -q 'data:image/webp;base64,' "$post"
  grep -q 'srcset="[^"]*\.webp 1200w, [^"]*\.webp 1800w"' "$post"
  if grep -q '2400w' "$post"; then
    fail "hero srcset still offers 2400w"
  fi
  grep -q 'property="og:image" content="[^"]*\.jpg"' "$post"
  grep -q 'rel="preload" as="image"' "$post"
  grep -q 'imagesizes="100vw"' "$post"
  grep -q 'fetchpriority="high"' "$post"
  grep -q 'processed_images/hero.' "$post"
  if grep -q 'og/why-a-blog-why-now.png' "$post"; then
    fail "generated hero used a title card over its picture"
  fi
else
  test -f "$public/og/why-a-blog-why-now.png"
  grep -q 'og/why-a-blog-why-now.png' "$post"
  if grep -q 'rel="preload" as="image"' "$post"; then
    fail "text post preloaded a hero"
  fi
  if grep -q 'data:image/webp;base64,' "$post"; then
    fail "text post inlined a hero preview"
  fi
fi

grep -q 'github.com/Jarvvski' "$about"
grep -q 'x.com/__adamjarvis' "$about"
grep -q '"@type": "Person"' "$about" || grep -q '"@type":"Person"' "$about"
grep -q 'post-list' "$home"
grep -q 'min read' "$home"
grep -q 'why-a-blog-why-now' "$home"
if ! awk '
  /class="meta"/ { grab = 1; buf = "" }
  grab { buf = buf $0 "\n" }
  grab && /<\/div>/ {
    if (buf ~ /class="meta-line"/ && buf ~ /class="tags"/ && buf ~ /min read/ && buf ~ /tags\/writing\//) ok = 1
    exit
  }
  END { exit !ok }
' "$home"; then
  fail "home tags are not on the meta row"
fi
if awk '
  /<p class="summary">/ { summary = 1 }
  summary && /class="tags"/ { found = 1 }
  END { exit !found }
' "$home"; then
  fail "home tags sit below the summary"
fi
grep -q 'class="site-name"[^>]*>Adam</a>' "$home"
grep -q '<h1>Adam</h1>' "$home"
grep -q '<title>Adam Jarvis</title>' "$home"
grep -q '<p>Adam Jarvis</p>' "$home"
grep -q "I'm Adam Jarvis" "$about"
grep -q '<title>Adam Jarvis</title>' "$public/atom.xml"
grep -q '<author>Adam Jarvis</author>' "$public/rss.xml"
grep -q 'pagefind-ui.js' "$search"
grep -q 'jarvis.gg' "$public/CNAME"
grep -q 'Sitemap: https://jarvis.gg/sitemap.xml' "$public/robots.txt"
grep -q 'prefers-reduced-motion' "$public/style.css"
grep -q 'Source Serif 4' "$public/style.css"
grep -qi '#191919' "$public/style.css"
grep -qi '#7aa2f7' "$public/style.css"
grep -qi '#c0caf5' "$public/giallo.css"
if grep -q '#1c1d21' "$public/style.css"; then
  fail "old page grey remains"
fi
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
