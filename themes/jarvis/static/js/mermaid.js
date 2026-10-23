var darkVars = {
  background: "transparent",
  primaryColor: "#24283b",
  primaryTextColor: "#c0caf5",
  primaryBorderColor: "#3b4261",
  secondaryColor: "#292e42",
  secondaryTextColor: "#a9b1d6",
  tertiaryColor: "#1a1b26",
  tertiaryTextColor: "#c0caf5",
  lineColor: "#a9b1d6",
  textColor: "#c0caf5",
  mainBkg: "#24283b",
  nodeBorder: "#3b4261",
  clusterBkg: "#1a1b26",
  titleColor: "#c0caf5",
  edgeLabelBackground: "#1a1b26"
};

function hosts() {
  document.querySelectorAll('code[data-lang="mermaid"]').forEach(function (code) {
    var pre = code.closest("pre");
    if (!pre || pre.dataset.mermaidReady === "true") return;
    var host = document.createElement("div");
    host.className = "mermaid-host";
    host.dataset.source = code.textContent.replace(/\n$/, "");
    pre.replaceWith(host);
  });
  return document.querySelectorAll(".mermaid-host");
}

var mermaidApi = null;

async function renderMermaid() {
  var nodes = hosts();
  if (!nodes.length) return;
  if (!mermaidApi) {
    var mod = await import("https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.esm.min.mjs");
    mermaidApi = mod.default;
  }
  mermaidApi.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "base",
    themeVariables: darkVars
  });
  for (var i = 0; i < nodes.length; i++) {
    var host = nodes[i];
    var id = "diagram-" + i;
    var result = await mermaidApi.render(id, host.dataset.source);
    host.innerHTML = result.svg;
  }
}

window.renderMermaid = renderMermaid;
renderMermaid();
