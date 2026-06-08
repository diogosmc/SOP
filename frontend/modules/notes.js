/** @param {string} text */
export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** @param {string} raw */
export function parseTagsInput(raw) {
  return raw
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

/** @param {string[]|null|undefined} tags */
export function tagsToInput(tags) {
  if (!tags || !tags.length) return "";
  return tags.join(", ");
}

/** @param {object} form */
export function noteFormToPayload(form) {
  const tags = parseTagsInput(form.tags);
  const payload = {
    title: form.title.trim(),
    content: form.content || "",
    favorite: Boolean(form.favorite),
    archived: Boolean(form.archived),
  };
  if (tags.length) payload.tags = tags;
  else payload.tags = [];
  return payload;
}

/** @param {string} markdown */
export function renderMarkdown(markdown) {
  if (!markdown) {
    return '<p class="md-preview__empty">Sem conteúdo.</p>';
  }

  const lines = markdown.split("\n");
  const parts = [];
  let listOpen = false;

  const closeList = () => {
    if (listOpen) {
      parts.push("</ul>");
      listOpen = false;
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();

    if (!trimmed) {
      closeList();
      continue;
    }

    if (trimmed.startsWith("# ")) {
      closeList();
      parts.push(`<h1>${inlineMarkdown(trimmed.slice(2))}</h1>`);
      continue;
    }
    if (trimmed.startsWith("## ")) {
      closeList();
      parts.push(`<h2>${inlineMarkdown(trimmed.slice(3))}</h2>`);
      continue;
    }
    if (trimmed.startsWith("### ")) {
      closeList();
      parts.push(`<h3>${inlineMarkdown(trimmed.slice(4))}</h3>`);
      continue;
    }
    if (trimmed.startsWith("- ")) {
      if (!listOpen) {
        parts.push("<ul>");
        listOpen = true;
      }
      parts.push(`<li>${inlineMarkdown(trimmed.slice(2))}</li>`);
      continue;
    }

    closeList();
    parts.push(`<p>${inlineMarkdown(trimmed)}</p>`);
  }

  closeList();
  return parts.join("\n");
}

/** @param {string} text */
function inlineMarkdown(text) {
  let html = escapeHtml(text);
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  return html;
}

/** @param {number} value */
export function formatSimilarity(value) {
  if (typeof value !== "number") return "—";
  return `${Math.round(value * 100)}%`;
}

/** @param {string|null|undefined} iso */
export function formatNoteDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** @param {string} text @param {number} [max] */
export function excerpt(text, max = 120) {
  const plain = String(text || "").replace(/\s+/g, " ").trim();
  if (plain.length <= max) return plain;
  return `${plain.slice(0, max)}…`;
}
