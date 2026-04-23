// Tiny passcode wrapper — shared passcode in localStorage, prompt() on first use.
// Storage key: lp.passcode
// Usage: passcode.get() → string; passcode.clear() to forget (wrong-passcode path).

const KEY = "lp.passcode";

export const passcode = {
  get() {
    let v = localStorage.getItem(KEY);
    if (!v) {
      v = window.prompt("Enter teacher passcode:") ?? "";
      if (v) localStorage.setItem(KEY, v);
    }
    return v;
  },

  clear() {
    localStorage.removeItem(KEY);
  },
};
