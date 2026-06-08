/** @typedef {{ id: string, name: string, email: string, is_admin: boolean }} AuthUser */

export function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** @param {AuthUser|null} user */
export function userLabel(user) {
  if (!user) return "Convidado";
  return user.name || user.email || "Usuário";
}
