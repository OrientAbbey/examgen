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
  if (r.status === 429) { $('#statut').textContent = 'Trop de requêtes. Patientez un instant.'; return; }
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
  renderMath(box);                           // KaTeX : indices, exposants, fractions, formules chimiques
  $('#epreuve').hidden = false;
  $('#epreuve').scrollIntoView({ behavior: 'smooth' });
}
// ───── Assistant IA (facultatif : n'apparaît que s'il est configuré et ouvert au public) ─────
async function initIA() {
  let st;
  try { st = await (await fetch('/api/ai/status')).json(); } catch { return; }
  if (!st.actif || !st.public) return;
  $('#assistant').hidden = false; $('#bareme').hidden = false;
  $('#ia-go').addEventListener('click', iaRemplir);
  $('#bareme').addEventListener('click', iaBareme);
}
function iaMessage(t) { $('#ia-msg').textContent = t; }
async function iaRemplir() {
  const texte = $('#ia-texte').value.trim();
  if (texte.length < 3) return;
  $('#ia-go').disabled = true; iaMessage('⏳ L\'assistant lit votre demande…');
  let r;
  try { r = await fetch('/api/ai/parametres', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ texte }) }); }
  catch { iaMessage('Assistant indisponible pour le moment.'); $('#ia-go').disabled = false; return; }
  $('#ia-go').disabled = false;
  if (!r.ok) { iaMessage(r.status === 429 ? 'Trop de demandes, patientez un instant.' : 'Assistant indisponible pour le moment.'); return; }
  const j = await r.json();
  if (j.matiereId) $('#matiere').value = j.matiereId;
  if (j.classeId) $('#classe').value = j.classeId;
  if (j.specialiteId) $('#specialite').value = j.specialiteId;
  if (j.session) $('#session').value = j.session;
  if (j.difficulte) { const d = document.querySelector('input[name=diff][value=' + j.difficulte + ']'); if (d) d.checked = true; }
  refresh();
  const manque = [!j.matiereId && 'la matière', !j.classeId && 'la classe', !j.difficulte && 'la difficulté'].filter(Boolean);
  iaMessage((j.explication || 'Formulaire rempli.') + (manque.length ? ' Complétez : ' + manque.join(', ') + '.' : ' Vérifiez puis cliquez sur Générer.'));
  if ($('#ia-auto').checked && valide()) generer(false);
}
async function iaBareme() {
  if (!urls) return;
  const gid = urls.epreuve.split('/').pop(), out = $('#bareme-out');
  out.textContent = '⏳ L\'assistant propose un barème…';
  let r;
  try { r = await fetch('/api/epreuve/' + gid + '/assistant', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'bareme' }) }); }
  catch { out.textContent = 'Assistant indisponible pour le moment.'; return; }
  if (!r.ok) { out.textContent = r.status === 429 ? 'Trop de demandes, patientez un instant.' : 'Assistant indisponible pour le moment.'; return; }
  const j = await r.json(), t = document.createElement('table'); t.className = 'bareme';
  const ligne = (...c) => { const tr = document.createElement('tr'); c.forEach(x => { const td = document.createElement('td'); td.textContent = x; tr.append(td); }); t.append(tr); };
  ligne('Exercice', 'Points', 'Détail');
  j.exercices.forEach(e => ligne('Exercice ' + e.numero, String(e.points).replace('.', ','), e.questions.map(q => q.q + ' : ' + String(q.points).replace('.', ',')).join(' · ')));
  ligne('Total', String(j.total).replace('.', ',') + ' pts', j.dureeMinutes ? 'Durée suggérée : ' + j.dureeMinutes + ' min' : '');
  const p = document.createElement('p'); p.className = 'mut'; p.textContent = (j.remarques || '') + ' (Proposition de l\'assistant : à adapter.)';
  out.replaceChildren(t, p);
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
  initIA();
}
init();
