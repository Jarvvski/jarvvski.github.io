(function () {
  try {
    localStorage.removeItem("theme");
  } catch (e) {}

  var header = document.querySelector(".site-header");
  var hero = document.querySelector("header.hero");
  if (header && hero) {
    var onHeroScroll = function () {
      var past = hero.getBoundingClientRect().bottom <= header.offsetHeight;
      header.classList.toggle("is-solid", past);
      document.body.classList.toggle("is-scrolled", past);
    };
    onHeroScroll();
    window.addEventListener("scroll", onHeroScroll, { passive: true });
    window.addEventListener("resize", onHeroScroll);
  }

  var bar = document.querySelector(".progress > span");
  if (bar) {
    var onProgress = function () {
      var height = document.documentElement.scrollHeight - window.innerHeight;
      var amount = height > 0 ? Math.min(100, (window.scrollY / height) * 100) : 0;
      bar.style.width = amount + "%";
    };
    onProgress();
    window.addEventListener("scroll", onProgress, { passive: true });
  }

  var names = {
    rust: "Rust",
    kotlin: "Kotlin",
    go: "Go",
    javascript: "JavaScript",
    typescript: "TypeScript",
    python: "Python",
    html: "HTML",
    css: "CSS",
    bash: "Bash",
    sh: "Shell",
    toml: "TOML",
    json: "JSON",
    sql: "SQL",
    markdown: "Markdown"
  };

  document.querySelectorAll("pre.giallo").forEach(function (pre) {
    var code = pre.querySelector("code");
    var lang = (code && code.dataset.lang) || "";
    if (lang === "mermaid" || pre.closest(".codeblock")) return;
    var wrap = document.createElement("div");
    wrap.className = "codeblock";
    var barRow = document.createElement("div");
    barRow.className = "codeblock-bar";
    var label = document.createElement("span");
    label.textContent = names[lang] || lang;
    var button = document.createElement("button");
    button.type = "button";
    button.textContent = "Copy";
    button.addEventListener("click", function () {
      var text = code ? code.textContent : "";
      var done = function () {
        button.textContent = "Copied";
        window.setTimeout(function () {
          button.textContent = "Copy";
        }, 1600);
      };
      var fallback = function () {
        var area = document.createElement("textarea");
        area.value = text;
        area.setAttribute("readonly", "");
        area.style.position = "fixed";
        area.style.left = "-9999px";
        document.body.appendChild(area);
        area.select();
        var ok = false;
        try {
          ok = document.execCommand("copy");
        } catch (e) {
          ok = false;
        }
        document.body.removeChild(area);
        if (ok) done();
        else button.textContent = "Copy failed";
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fallback);
        return;
      }
      fallback();
    });
    barRow.appendChild(label);
    barRow.appendChild(button);
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(barRow);
    wrap.appendChild(pre);
  });
})();
