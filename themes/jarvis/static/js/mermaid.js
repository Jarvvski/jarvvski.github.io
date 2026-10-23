var darkVars = {
  background: "transparent",
  primaryColor: "#2f334d",
  primaryTextColor: "#c8d3f5",
  primaryBorderColor: "#3b4261",
  secondaryColor: "#222436",
  secondaryTextColor: "#c8d3f5",
  tertiaryColor: "#1e2030",
  tertiaryTextColor: "#c8d3f5",
  lineColor: "#82aaff",
  textColor: "#c8d3f5",
  mainBkg: "#2f334d",
  nodeBorder: "#82aaff",
  clusterBkg: "#1e2030",
  titleColor: "#c8d3f5",
  edgeLabelBackground: "#1e2030",
  nodeTextColor: "#c8d3f5"
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
