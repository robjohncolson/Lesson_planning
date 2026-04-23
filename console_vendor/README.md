# console_vendor

Build step for the CodeMirror 6 bundle shipped to the Teacher Console frontend.

## Rebuild

```bash
cd console_vendor
npm install            # first time only
npm run build          # → ../console_static/vendor/codemirror.js (~412 KB min.)
```

The bundled output is **committed** (see `console_static/vendor/codemirror.js`) so the
console runs offline without a build step on the teacher machine.

## Why bundled, not CDN

Phase 1 attempted CDN imports (`https://esm.sh/@codemirror/*`). Loading `codemirror`
(basicSetup) and `@codemirror/lang-yaml` separately over `+esm` caused two copies of
`@codemirror/state` in the module graph — `instanceof` checks against `EditorState`
silently returned false, and the editor refused to mount. A single esbuild bundle
forces one shared `@codemirror/state` instance.

## Entry points exported

See `entry.mjs` — keep this in sync with imports in `console_static/console.js`:

- `EditorView`, `EditorState`, `Compartment`, `keymap` (state + view)
- `basicSetup` (codemirror meta-package)
- `yaml` (lang-yaml)
- `indentWithTab` (commands)
