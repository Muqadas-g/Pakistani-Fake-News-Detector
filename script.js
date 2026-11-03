const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const MAX = 5000;
const LANGS = {
  en: { name: "English", rtl: false }, ur: { name: "Urdu", rtl: true },
  sd: { name: "Sindhi", rtl: true }, pa: { name: "Punjabi", rtl: true },
  skr: { name: "Saraiki", rtl: true }, rur: { name: "Roman Urdu", rtl: false },
};
let lang = "en", tab = "text";

// Theme
const root = document.documentElement;
root.dataset.theme = localStorage.getItem("theme") || "light";
const tg = $("#themeToggle");
function flipTheme() { root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark"; localStorage.setItem("theme", root.dataset.theme); }
tg.addEventListener("click", flipTheme);
tg.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); flipTheme(); } });

// Mobile menu
$("#menuBtn").addEventListener("click", () => { const o = $("#navLinks").classList.toggle("open"); $("#menuBtn").setAttribute("aria-expanded", o); });
$$("#navLinks a").forEach(a => a.addEventListener("click", () => { $("#navLinks").classList.remove("open"); $$("#navLinks a").forEach(x => x.classList.toggle("act", x === a)); }));

const bText = $("#analyzeText"), bUrl = $("#analyzeUrl"), ta = $("#newsText");

// Tabs
function setTab(t) {
  tab = t;
  $$(".tab").forEach(x => { const on = x.dataset.tab === t; x.classList.toggle("active", on); x.setAttribute("aria-selected", on); });
  $$(".panel").forEach(p => p.classList.toggle("active", p.id === "panel-" + t));
  bText.classList.toggle("hide", t === "url");
  bUrl.classList.toggle("outline", t === "text");
  bUrl.classList.toggle("solo", t === "url");
  clearMsg();
}
$$(".tab").forEach(t => t.addEventListener("click", () => setTab(t.dataset.tab)));
setTab("text");

// Languages (text never cleared on switch)
function applyLang() {
  $$(".lang").forEach(b => b.classList.toggle("active", b.dataset.lang === lang));
  ta.dir = LANGS[lang].rtl ? "rtl" : "ltr";
  ta.classList.toggle("urdu", LANGS[lang].rtl);
  $("#advLang").textContent = LANGS[lang].name + (LANGS[lang].rtl ? " (right-to-left)" : " (left-to-right)");
}
$$(".lang").forEach(b => b.addEventListener("click", () => { lang = b.dataset.lang; applyLang(); }));
applyLang();

// Counter / clear
function updateCount() { $("#counter").textContent = ta.value.length + " / " + MAX; }
ta.addEventListener("input", () => { updateCount(); clearMsg(); });
$("#clearBtn").addEventListener("click", () => { ta.value = ""; updateCount(); ta.focus(); hideResult(); clearMsg(); });
updateCount();

// Advanced
$("#advBtn").addEventListener("click", () => { const o = $("#advPanel").classList.toggle("open"); $("#advBtn").setAttribute("aria-expanded", o); });

function showMsg(t) { const m = $("#msg"); m.textContent = t; m.hidden = false; }
function clearMsg() { $("#msg").hidden = true; }
function setLoading(btn, on) { btn.classList.toggle("loading", on); btn.disabled = on; }
function validUrl(v) { try { const u = new URL(v); return u.protocol === "http:" || u.protocol === "https:"; } catch (_) { return false; } }

async function run(kind, input, btn) {
  setLoading(btn, true);
  try {
    const data = kind === "text" ? await analyzeText(input, lang) : await analyzeUrl(input, lang);
    renderResult(data, kind, input);
  } catch (e) {
    showMsg(kind === "url"
      ? "Could not fetch or analyze this article. " + (e.message || "") + " Try pasting the article text instead."
      : (e.message && e.message.startsWith("Server") ? e.message : "Something went wrong while analyzing. Please try again."));
  } finally { setLoading(btn, false); }
}

// Analyze News (text tab). A lone URL pasted here is routed to URL analysis.
bText.addEventListener("click", () => {
  clearMsg(); hideResult();
  const v = ta.value.trim();
  if (!v) return showMsg("Please paste some news text first.");
  if (validUrl(v) && !/\s/.test(v)) return run("url", v, bText);
  if (v.length < 20) return showMsg("Text is too short. Please add more content for a meaningful check.");
  if (v.length > MAX) return showMsg("Text is too long. Maximum is " + MAX + " characters.");
  run("text", v, bText);
});

// Analyze URL
bUrl.addEventListener("click", () => {
  clearMsg(); hideResult();
  if (tab === "text") {
    const v = ta.value.trim();
    if (v && validUrl(v) && !/\s/.test(v)) return run("url", v, bUrl);
    setTab("url"); $("#newsUrl").focus(); return;
  }
  const u = $("#newsUrl").value.trim();
  if (!u) return showMsg("Please enter a news article URL.");
  if (!validUrl(u)) return showMsg("That doesn't look like a valid URL. It must start with http:// or https://");
  run("url", u, bUrl);
});
$("#newsUrl").addEventListener("keydown", e => { if (e.key === "Enter") bUrl.click(); });

// Result
function hideResult() { $("#result").hidden = true; }
function renderResult(d, kind, input) {
  const fake = String(d.label).toLowerCase().includes("fake");
  const box = $("#result");
  box.className = "result " + (fake ? "fake" : "real");
  $("#resIcon").textContent = fake ? "✕" : "✓";
  $("#resLabel").textContent = fake ? "Fake News" : "Real News";
  let c = d.confidence; const cb = $("#confBox");
  if (typeof c === "number" && isFinite(c)) {
    if (c <= 1) c *= 100; c = Math.round(c * 10) / 10;
    cb.hidden = false; $("#confVal").textContent = c + "%"; $("#confFill").style.width = c + "%";
  } else cb.hidden = true;
  $("#resLang").textContent = LANGS[lang].name;
  $("#resType").textContent = kind === "url" ? "URL" : "Text";
  $("#resTime").textContent = new Date().toLocaleString();
  const src = $("#resSrc"); src.hidden = kind !== "url"; if (kind === "url") src.querySelector("b").textContent = input;
  $("#demoTag").hidden = !d.mock;
  $("#resDetails").hidden = !$("#showDetails").checked;
  box.hidden = false;
  box.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Ticker
const msgs = ["Stay informed! Verify news before you share.", "Read. Verify. Trust.", "Predictions can be wrong, check reliable sources."];
let mi = 0;
setInterval(() => {
  const el = $("#tickerText"); el.classList.add("out");
  setTimeout(() => { mi = (mi + 1) % msgs.length; el.textContent = msgs[mi]; el.classList.remove("out"); }, 400);
}, 4500);

// Reveal
const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { threshold: .12 });
$$(".reveal").forEach(el => io.observe(el));
$("#year").textContent = new Date().getFullYear();
