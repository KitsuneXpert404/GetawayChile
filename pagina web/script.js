const root = document.documentElement;
const menuBtn = document.getElementById("menuBtn");
const mainNav = document.getElementById("mainNav");
const yearNode = document.getElementById("year");
const progress = document.getElementById("scrollProgress");
const revealElements = document.querySelectorAll("[data-reveal]");
const counterElements = document.querySelectorAll("[data-counter]");
const tiltElements = document.querySelectorAll(".tilt");
const reserveForms = document.querySelectorAll("[data-reserva-form]");

const LANG_STORAGE_KEY = "gw_lang";
const TRANSLATION_CACHE_PREFIX = "gw_translate_cache_v2_";
const DEFAULT_LANG = "es";
const TRANSLATE_ENDPOINT = "https://translate.googleapis.com/translate_a/single";
const LANGS = [
  { code: "es", label: "ES" },
  { code: "en", label: "EN" },
  { code: "pt", label: "PT" }
];

const NAV_ITEMS = [
  { href: "index.html", key: "inicio", label: "Inicio" },
  { href: "tours.html", key: "tours", label: "Tours" },
  { href: "tours-privados.html", key: "tours_privados", label: "Tours Privados" },
  { href: "aeropuerto.html", key: "aeropuerto", label: "Aeropuerto" },
  { href: "reservas.html", key: "reservas", label: "Reservas" }
];

const FOOTER_LINK_ITEMS = [
  { href: "index.html", label: "Inicio" },
  { href: "tours.html", label: "Tours" },
  { href: "tours-privados.html", label: "Tours Privados" },
  { href: "aeropuerto.html", label: "Aeropuerto" },
  { href: "reservas.html", label: "Reservas" }
];

const i18nState = {
  textNodes: [],
  attrNodes: [],
  originals: [],
  ready: false,
  working: false
};

if (yearNode) {
  yearNode.textContent = new Date().getFullYear().toString();
}

const currentFile = () => {
  const file = window.location.pathname.split("/").pop();
  return file || "index.html";
};

const activeNavKey = () => {
  const file = currentFile();
  if (file.startsWith("tour-")) return "tours";
  if (file.startsWith("servicio-")) {
    if (file.includes("aeropuerto")) return "aeropuerto";
    return "tours_privados";
  }
  if (file === "aeropuerto.html") return "aeropuerto";
  if (file === "tours-privados.html") return "tours_privados";
  if (file === "tours.html") return "tours";
  if (file === "reservas.html") return "reservas";
  return "inicio";
};

const buildNavigation = () => {
  if (!mainNav) return;
  const active = activeNavKey();
  mainNav.innerHTML = NAV_ITEMS
    .map((item) => `<a href="${item.href}" class="${item.key === active ? "active" : ""}">${item.label}</a>`)
    .join("");
};

if (menuBtn && mainNav) {
  menuBtn.addEventListener("click", () => {
    const isOpen = mainNav.classList.toggle("open");
    menuBtn.setAttribute("aria-expanded", String(isOpen));
    document.body.classList.toggle("menu-open", isOpen);
  });

  mainNav.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLAnchorElement)) return;
    mainNav.classList.remove("open");
    menuBtn.setAttribute("aria-expanded", "false");
    document.body.classList.remove("menu-open");
  });
}

if (progress) {
  const updateProgress = () => {
    const scrollTop = window.scrollY;
    const total = document.body.scrollHeight - window.innerHeight;
    const value = total > 0 ? (scrollTop / total) * 100 : 0;
    progress.style.width = `${value}%`;
  };
  updateProgress();
  window.addEventListener("scroll", updateProgress, { passive: true });
}

if (revealElements.length) {
  const revealObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.15 }
  );
  revealElements.forEach((element) => revealObserver.observe(element));
}

const animateCounter = (element) => {
  const target = Number(element.dataset.counter || 0);
  const suffix = element.dataset.suffix || "+";
  const duration = 1600;
  const start = performance.now();

  const step = (time) => {
    const progressValue = Math.min((time - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progressValue, 3);
    const current = Math.round(target * eased);
    element.textContent = `${current}${suffix}`;
    if (progressValue < 1) requestAnimationFrame(step);
  };

  requestAnimationFrame(step);
};

if (counterElements.length) {
  const counterObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.7 }
  );
  counterElements.forEach((counter) => counterObserver.observe(counter));
}

const heroHome = document.querySelector(".hero-home");
if (heroHome) {
  heroHome.addEventListener("mousemove", (event) => {
    const rect = heroHome.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    root.style.setProperty("--mouse-x", `${x}px`);
    root.style.setProperty("--mouse-y", `${y}px`);
  });
}

tiltElements.forEach((card) => {
  card.addEventListener("mousemove", (event) => {
    const rect = card.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const rotateX = (event.clientY - centerY) / 22;
    const rotateY = (centerX - event.clientX) / 22;
    card.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
  });
  card.addEventListener("mouseleave", () => {
    card.style.transform = "rotateX(0) rotateY(0)";
  });
});

reserveForms.forEach((form) => {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const getValue = (selector) => form.querySelector(selector)?.value?.trim() || "";
    const name = getValue('input[name="nombre"]') || "Sin nombre";
    const phone = getValue('input[name="telefono"]') || "Sin telefono";
    const service = getValue('select[name="servicio"]') || "Servicio no especificado";
    const people = getValue('input[name="personas"]') || "Sin dato";
    const date = getValue('input[name="fecha"]') || "Sin fecha";
    const message = getValue('textarea[name="mensaje"]') || "Sin mensaje adicional";
    const text = encodeURIComponent(
      `Hola Getaway Chile, quiero reservar/cotizar:\n- Nombre: ${name}\n- Telefono: ${phone}\n- Servicio: ${service}\n- Personas: ${people}\n- Fecha: ${date}\n- Mensaje: ${message}`
    );
    window.open(`https://wa.me/56994155655?text=${text}`, "_blank", "noopener");
  });
});

const addFooterEnhancements = () => {
  document.querySelectorAll(".site-footer").forEach((footer) => {
    if (!footer.querySelector(".footer-badges")) {
      const badges = document.createElement("div");
      badges.className = "footer-badges container";
      badges.innerHTML = `
        <span>Atencion 24/7</span>
        <span>Flota ejecutiva</span>
        <span>Conductores profesionales</span>
      `;
      footer.insertBefore(badges, footer.querySelector(".copyright"));
    }

    if (!footer.querySelector(".footer-note")) {
      const note = document.createElement("p");
      note.className = "footer-note";
      note.textContent = "Precios referenciales en USD / CLP / BRL. Confirmar valor final al reservar.";
      footer.insertBefore(note, footer.querySelector(".copyright"));
    }

    if (!footer.querySelector(".footer-extra-links")) {
      const container = document.createElement("div");
      container.className = "container footer-extra-links";
      container.style.display = "flex";
      container.style.flexWrap = "wrap";
      container.style.gap = "0.55rem";
      container.style.justifyContent = "center";
      container.style.marginTop = "0.8rem";
      container.innerHTML = FOOTER_LINK_ITEMS.map((item) => `<a href="${item.href}" class="btn-outline">${item.label}</a>`).join("");
      footer.insertBefore(container, footer.querySelector(".copyright"));
    }
  });
};

const formatCLP = (value) => `CLP $${Math.round(value).toLocaleString("es-CL")}`;
const formatBRL = (value) => `BRL R$ ${Math.round(value).toLocaleString("pt-BR")}`;

const renderMultiCurrencyPrices = () => {
  const USD_TO_CLP = 950;
  const USD_TO_BRL = 5.1;

  document.querySelectorAll(".price-row span:last-child, .tour-meta span:first-child").forEach((node) => {
    if (!node.dataset.basePrice) node.dataset.basePrice = node.textContent.trim();
    const baseText = node.dataset.basePrice;
    const match = baseText.match(/USD\s*([0-9]+)/i);
    if (!match) return;

    const usdValue = Number(match[1]);
    const fromPrefix = /desde|from|a partir/i.test(baseText) ? "Desde " : "";
    node.textContent = `${fromPrefix}USD ${usdValue} | ${formatCLP(usdValue * USD_TO_CLP)} | ${formatBRL(usdValue * USD_TO_BRL)}`;
  });
};

const isTranslatableText = (value) => {
  if (!value || !value.trim()) return false;
  const clean = value.trim();
  if (/^[0-9\s.,:/+\-()%$RCLPUSDhH]+$/.test(clean)) return false;
  return true;
};

const captureOriginalNodes = () => {
  if (i18nState.ready) return;

  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode: (node) => {
      const parent = node.parentElement;
      if (!parent) return NodeFilter.FILTER_REJECT;
      if (["SCRIPT", "STYLE", "NOSCRIPT", "SVG", "PATH"].includes(parent.tagName)) return NodeFilter.FILTER_REJECT;
      if (parent.closest(".lang-switch")) return NodeFilter.FILTER_REJECT;
      if (!isTranslatableText(node.nodeValue || "")) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }
  });

  let current = walker.nextNode();
  while (current) {
    const original = current.nodeValue || "";
    i18nState.textNodes.push({ node: current, original });
    i18nState.originals.push(original.trim());
    current = walker.nextNode();
  }

  document.querySelectorAll("[placeholder],[title],[aria-label],[alt]").forEach((element) => {
    ["placeholder", "title", "aria-label", "alt"].forEach((attr) => {
      const value = element.getAttribute(attr);
      if (!isTranslatableText(value || "")) return;
      i18nState.attrNodes.push({ element, attr, original: value || "" });
      i18nState.originals.push((value || "").trim());
    });
  });

  i18nState.ready = true;
};

const loadLangCache = (lang) => {
  try {
    const raw = localStorage.getItem(`${TRANSLATION_CACHE_PREFIX}${lang}`);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
};

const saveLangCache = (lang, cache) => {
  try {
    localStorage.setItem(`${TRANSLATION_CACHE_PREFIX}${lang}`, JSON.stringify(cache));
  } catch {
    // ignore storage limits
  }
};

const extractGoogleText = (payload) => {
  if (!Array.isArray(payload) || !Array.isArray(payload[0])) return "";
  return payload[0].map((part) => (Array.isArray(part) ? part[0] || "" : "")).join("");
};

const translateRequest = async (text, targetLang) => {
  const params = new URLSearchParams({
    client: "gtx",
    sl: "es",
    tl: targetLang,
    dt: "t",
    q: text
  });
  const response = await fetch(`${TRANSLATE_ENDPOINT}?${params.toString()}`);
  if (!response.ok) throw new Error("translate_request_failed");
  const payload = await response.json();
  return extractGoogleText(payload);
};

const chunkByLength = (texts, maxLen = 1400) => {
  const chunks = [];
  let current = [];
  let len = 0;
  texts.forEach((text) => {
    const extra = text.length + 12;
    if (len + extra > maxLen && current.length) {
      chunks.push(current);
      current = [];
      len = 0;
    }
    current.push(text);
    len += extra;
  });
  if (current.length) chunks.push(current);
  return chunks;
};

const translateMissingStrings = async (missingTexts, targetLang, cache) => {
  const delimiter = "\n[[[GW_SPLIT]]]\n";
  const chunks = chunkByLength(missingTexts, 1200);

  for (const chunk of chunks) {
    try {
      const combined = chunk.join(delimiter);
      const translatedCombined = await translateRequest(combined, targetLang);
      const parts = translatedCombined.split("[[[GW_SPLIT]]]");
      if (parts.length === chunk.length) {
        chunk.forEach((source, index) => {
          cache[source] = (parts[index] || "").trim();
        });
      } else {
        for (const source of chunk) {
          cache[source] = (await translateRequest(source, targetLang)).trim();
        }
      }
    } catch {
      for (const source of chunk) {
        try {
          cache[source] = (await translateRequest(source, targetLang)).trim();
        } catch {
          cache[source] = source;
        }
      }
    }
  }
};

const applyTranslatedText = (lang, cache) => {
  if (lang === "es") {
    i18nState.textNodes.forEach((entry) => {
      entry.node.nodeValue = entry.original;
    });
    i18nState.attrNodes.forEach((entry) => {
      entry.element.setAttribute(entry.attr, entry.original);
    });
    document.documentElement.lang = "es";
    return;
  }

  i18nState.textNodes.forEach((entry) => {
    const original = entry.original;
    const trimmed = original.trim();
    const translated = cache[trimmed];
    if (!translated) return;
    const leading = original.match(/^\s*/)?.[0] || "";
    const trailing = original.match(/\s*$/)?.[0] || "";
    entry.node.nodeValue = `${leading}${translated}${trailing}`;
  });

  i18nState.attrNodes.forEach((entry) => {
    const translated = cache[(entry.original || "").trim()];
    if (translated) entry.element.setAttribute(entry.attr, translated);
  });

  document.documentElement.lang = lang;
};

const updateLangButtons = (lang) => {
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });
};

const applyLanguage = async (lang) => {
  if (i18nState.working) return;
  i18nState.working = true;
  localStorage.setItem(LANG_STORAGE_KEY, lang);
  updateLangButtons(lang);

  captureOriginalNodes();

  if (lang === "es") {
    applyTranslatedText("es", {});
    i18nState.working = false;
    return;
  }

  const cache = loadLangCache(lang);
  const uniqueOriginals = Array.from(new Set(i18nState.originals.filter((text) => text && text.trim())));
  const missing = uniqueOriginals.filter((text) => !cache[text]);

  if (missing.length) {
    await translateMissingStrings(missing, lang, cache);
    saveLangCache(lang, cache);
  }

  applyTranslatedText(lang, cache);
  i18nState.working = false;
};

const createNavbarLanguageSwitcher = () => {
  const actions = document.querySelector(".nav-actions");
  if (!actions || actions.querySelector(".lang-switch")) return;

  const row = document.createElement("div");
  row.className = "lang-switch";
  LANGS.forEach((lang) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "lang-btn";
    button.dataset.lang = lang.code;
    button.textContent = lang.label;
    button.addEventListener("click", () => {
      applyLanguage(lang.code);
    });
    row.appendChild(button);
  });

  actions.append(row);
};

buildNavigation();
addFooterEnhancements();
renderMultiCurrencyPrices();
createNavbarLanguageSwitcher();

const storedLang = localStorage.getItem(LANG_STORAGE_KEY) || DEFAULT_LANG;
const safeLang = LANGS.some((lang) => lang.code === storedLang) ? storedLang : DEFAULT_LANG;
applyLanguage(safeLang);
