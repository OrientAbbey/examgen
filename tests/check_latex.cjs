// Valide chaque formule avec le MÊME KaTeX (+ mhchem + macros) que celui servi au navigateur.
// Usage : node check_latex.cjs <dossier katex> < fragments.json   →  {checked, bad:[{tex,error}]}
const Module = require('module'), path = require('path'), fs = require('fs');
const dir = path.resolve(process.argv[2]), kpath = path.join(dir, 'katex.min.js');
const orig = Module._resolveFilename;
Module._resolveFilename = function (req, ...a) { return req === 'katex' ? kpath : orig.call(this, req, ...a); };
const katex = require(kpath);
require(path.join(dir, 'mhchem.min.js'));
require(path.join(dir, 'macros.js'));
const items = JSON.parse(fs.readFileSync(0, 'utf8')), bad = [];
for (const it of items) {
  try { katex.renderToString(it.tex, { displayMode: !!it.block, throwOnError: true, strict: 'ignore', macros: Object.assign({}, globalThis.KATEX_MACROS) }); }
  catch (e) { bad.push({ tex: it.tex, error: String(e.message).slice(0, 200) }); }
}
console.log(JSON.stringify({ checked: items.length, bad }));
