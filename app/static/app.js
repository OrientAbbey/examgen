const $ = s => document.querySelector(s);
let meta = null, last = null, urls = null;

function fill(sel, items, empty) {
  sel.replaceChildren();
  if (empty !== undefined) sel.append(new Option(empty, ''));
  for (const it of items) sel.append(new Option(it.nom, it.id));
}
function params() {
  const d = document.querySelector('input[name=diff]:checked');
  return { matiereId: $('#matiere').value, classeId: $('#classe').value,
    specialiteId: $('#specialite').value || null, session: $('#session').value || null,
    difficulte: d ? d.value : null };
}
function valide() {
  const p = params(), c = meta && meta.classes.find(x => x.id === p.classeId);
  return !!(p.matiereId && p.classeId && p.difficulte && (!c || !c.specialiteObligatoire || p.specialiteId));
}
function refresh() {
  const c = meta.classes.find(x => x.id === $('#classe').value);
  $('#spec-req').textContent = c && c.specialiteObligatoire ? '*' : '';
  $('#generer').disabled = !valide();       // aucun message : le bouton reste simplement inactif (cahier 2.2, §6)
}
async function generer(reuse) {
  if (!reuse && !valide()) return;
  $('#statut').textContent = '';
  last = reuse === true && last ? last : params();
  let r;
  try { r = await fetch('/api/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(last) }); }
  catch { $('#statut').textContent = 'Service indisponible. Réessayez.'; return; }
  if (r.status >= 500) { $('#statut').textContent = 'Service indisponible. Réessayez.'; return; }
  if (!r.ok) return;                         // cas métier : silence
  const j = await r.json();
  urls = j.urls;
  const box = $('#exos'); box.replaceChildren();
  for (const e of j.exercices) {
    const s = document.createElement('section'); s.className = 'exo';
    const h = document.createElement('h3'); h.textContent = 'Exercice ' + e.numero;
    const d = document.createElement('div'); d.className = 'md'; d.innerHTML = e.sujetHtml;  // HTML issu de markdown-it (html brut désactivé)
    s.append(h, d); box.append(s);
  }
  $('#epreuve').hidden = false;
  $('#epreuve').scrollIntoView({ behavior: 'smooth' });
}
async function init() {
  try { meta = await (await fetch('/api/meta')).json(); }
  catch { $('#statut').textContent = 'Service indisponible. Réessayez.'; return; }
  fill($('#matiere'), meta.matieres, '— Choisir —');
  fill($('#classe'), meta.classes, '— Choisir —');
  fill($('#specialite'), meta.specialites, '— Aucune —');
  document.querySelector('#form').addEventListener('input', refresh);
  $('#generer').addEventListener('click', () => generer(false));
  $('#regenerer').addEventListener('click', () => generer(true));   // mêmes paramètres, nouveau tirage
  $('#imprimer').addEventListener('click', () => urls && window.open(urls.imprimer, '_blank', 'noopener'));
  $('#corrige').addEventListener('click', () => urls && window.open(urls.corrige, '_blank', 'noopener'));
  refresh();
}
init();
