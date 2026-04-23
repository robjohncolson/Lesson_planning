// Username wrapper — teacher display name stored in localStorage, prompted once.
// Storage key: lp.username
// Usage: username.get() → string; username.clear() to re-prompt (change name).

const KEY = "lp.username";

function isValid(v) {
  if (!v || !v.trim()) return false;
  if (v.length > 40) return false;
  if (/[\r\n]/.test(v)) return false;
  return true;
}

export const username = {
  get() {
    let v = localStorage.getItem(KEY);
    while (!isValid(v)) {
      v = (window.prompt("Enter your display name (shown on edits):") ?? "").trim();
      if (isValid(v)) {
        localStorage.setItem(KEY, v);
      } else {
        // empty prompt = user cancelled; store nothing and return empty string
        // so callers get a safe value rather than looping forever on Cancel
        if (v === "") return "";
      }
    }
    return v;
  },

  clear() {
    localStorage.removeItem(KEY);
  },
};
