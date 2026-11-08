const $ = (s, r = document) => r.querySelector(s);
function el(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === false || v == null) continue;
    if (k === 'class') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else if (k === 'value') e.value = v;
    else if (k === 'checked') e.checked = !!v;
    else e.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat()) e.append(kid instanceof Node ? kid : document.createTextNode(kid ?? ''));
  return e;
}
let TOKEN = sessionStorage.getItem('adm') || '';
async function api(method, path, body) {
  const r = await fetch('/api/admin' + path, { method, headers: { 'X-Admin-Token': TOKEN, ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}) },
    body: body !== undefined ? JSON.stringify(body) : undefined });
  let data = null; try { data = await r.json(); } catch {}
  if (r.status === 401) { await login(); return api(method, path, body); }
  return { ok: r.ok, status: r.status, data };
}
let loginP = null;       // une seule saisie de jeton à la fois, même si plusieurs requêtes échouent en parallèle
function login() {
  if (!loginP) loginP = (async () => {
    const inp = el('input', { type: 'password', autocomplete: 'current-password', placeholder: 'Jeton administrateur' });
    const ok = await ask('Connexion administrateur', b => b.append(inp));
    loginP = null;
    if (!ok || !inp.value) throw new Error('annulé');
    TOKEN = inp.value; sessionStorage.setItem('adm', TOKEN);
  })();
  return loginP;
}
function err(r) {
  const d = r.data || {};
  const det = Array.isArray(d.detail) ? d.detail.map(x => (x.loc || []).slice(1).join('.') + ' : ' + x.msg).join('\n- ') : '';
  alert((d.message || (det ? 'Données invalides' : d.code) || 'Erreur ' + r.status) + (det ? '\n- ' + det : '') + (d.errors ? '\n- ' + d.errors.join('\n- ') : ''));
}
function ask(title, build) {              // dialogue générique ; build(body) remplit le corps ; retourne true si validé
  return new Promise(res => {
    const dlg = $('#dlg'); $('#dlg-t').textContent = title; const b = $('#dlg-b'); b.replaceChildren(); build(b);
    dlg.returnValue = '';      // sinon Échap hériterait de la valeur du dialogue précédent
    dlg.onclose = () => res(dlg.returnValue === 'ok'); dlg.showModal();
  });
}
// Suppression avec blocage d'intégrité puis réaffectation explicite (cahier 3.1)
async function supprimer(path, label, targets, withPartie) {
  if (!confirm(`Supprimer « ${label} » ?`)) return false;
  let r = await api('DELETE', path);
  if (r.status === 409 && r.data.code === 'REFERENCED') {
    if (!targets.length) { alert(`« ${label} » est référencé par ${r.data.count} élément(s) et aucune cible de réaffectation n'existe.`); return false; }
    const sel = el('select', {}, targets.map(t => el('option', { value: t.id }, t.nom)));
    const sel2 = el('select', {});
    if (withPartie) {
      const load = async () => { const ps = (await api('GET', '/parties?matiereId=' + sel.value)).data || []; sel2.replaceChildren(...ps.map(p => el('option', { value: p.id }, p.nom))); };
      sel.addEventListener('change', load); await load();
    }
    const ok = await ask(`« ${label} » est référencé par ${r.data.count} élément(s). Réaffecter vers :`, b => b.append(sel, withPartie ? sel2 : ''));
    if (!ok) return false;
    const q = new URLSearchParams({ reassignTo: sel.value }); if (withPartie) q.set('reassignPartieId', sel2.value);
    r = await api('DELETE', path + '?' + q);
  }
  if (!r.ok) { err(r); return false; }
  return true;
}
const SEQ = ['', 1, 2, 3, 4, 5, 6];
const host = $('#view');
const TABS = { 'Matières & parties': tMatieres, Classes: tClasses, Spécialités: tSpecialites, Exercices: tExercices, 'Médias': tMedias, 'Import / Export': tIO, Journal: tJournal, Réglages: tReglages };
let current = 'Matières & parties';
function nav() {
  $('#tabs').replaceChildren(...Object.keys(TABS).map(k => el('button', { class: k === current ? 'on' : '', onclick: () => { current = k; nav(); } }, k)));
  // Chaque rendu dessine dans SON conteneur : une réponse tardive d'un rendu périmé ne peut plus polluer l'écran.
  const root = el('div'); host.replaceChildren(root);
  TABS[current](root).catch(e => root.append(e.message === 'annulé'
    ? el('p', {}, el('button', { class: 'primary', onclick: nav }, 'Se connecter'))
    : el('p', { class: 'mut' }, 'Erreur : ' + e.message)));
}
const nameForm = (ph, onadd) => { const i = el('input', { type: 'text', placeholder: ph }); return el('div', { class: 'row' }, i, el('button', { class: 'primary', onclick: async () => { if (i.value.trim()) await onadd(i.value.trim()); } }, 'Ajouter')); };

async function tMatieres(view) {
  const ms = (await api('GET', '/matieres')).data, ps = (await api('GET', '/parties')).data;
  view.append(el('div', { class: 'card' }, nameForm('Nouvelle matière', async n => { const r = await api('POST', '/matieres', { nom: n }); r.ok ? nav() : err(r); })));
  for (const m of ms) {
    const mine = ps.filter(p => p.matiereId === m.id);
    view.append(el('div', { class: 'card' },
      el('div', { class: 'row' }, el('strong', {}, m.nom), el('span', { class: 'badge' }, m.nbExercices + ' exercice(s)'),
        el('button', { onclick: async () => { const n = prompt('Nouveau nom', m.nom); if (n) { const r = await api('PUT', '/matieres/' + m.id, { nom: n }); r.ok ? nav() : err(r); } } }, 'Renommer'),
        el('button', { class: 'danger', onclick: async () => { if (await supprimer('/matieres/' + m.id, m.nom, ms.filter(x => x.id !== m.id), true)) nav(); } }, 'Supprimer')),
      el('table', { class: 't' }, mine.map(p => el('tr', {}, el('td', {}, p.ordre), el('td', {}, p.nom), el('td', {}, p.nbExercices + ' ex.'),
        el('td', {}, el('button', { onclick: async () => { const n = prompt('Nouveau nom', p.nom); if (n) { const r = await api('PUT', '/parties/' + p.id, { matiereId: m.id, nom: n, ordre: p.ordre }); r.ok ? nav() : err(r); } } }, 'Renommer'),
          ' ', el('button', { class: 'danger', onclick: async () => { if (await supprimer('/parties/' + p.id, p.nom, mine.filter(x => x.id !== p.id), false)) nav(); } }, 'Supprimer'))))),
      nameForm('Nouvelle partie', async n => { const r = await api('POST', '/parties', { matiereId: m.id, nom: n, ordre: mine.length + 1 }); r.ok ? nav() : err(r); })));
  }
}
async function tSpecialites(view) {
  const ss = (await api('GET', '/specialites')).data;
  view.append(el('div', { class: 'card' }, nameForm('Nouvelle spécialité', async n => { const r = await api('POST', '/specialites', { nom: n }); r.ok ? nav() : err(r); }),
    el('p', { class: 'mut' }, 'La valeur « Aucune » (exercice universel) est implicite et ne se supprime pas.'),
    el('table', { class: 't' }, ss.map(s => el('tr', {}, el('td', {}, s.nom), el('td', {}, s.nbExercices + ' ex.'),
      el('td', {}, el('button', { onclick: async () => { const n = prompt('Nouveau nom', s.nom); if (n) { const r = await api('PUT', '/specialites/' + s.id, { nom: n }); r.ok ? nav() : err(r); } } }, 'Renommer'), ' ',
        el('button', { class: 'danger', onclick: async () => { if (await supprimer('/specialites/' + s.id, s.nom, ss.filter(x => x.id !== s.id), false)) nav(); } }, 'Supprimer')))))));
}
async function tClasses(view) {
  const cs = (await api('GET', '/classes')).data;
  const nom = el('input', { type: 'text', placeholder: 'Nom de la classe' });
  const prev = el('select', {}, el('option', { value: '' }, 'Aucune'), cs.map(c => el('option', { value: c.id }, c.nom)));
  const ex = el('input', { type: 'checkbox' }), so = el('input', { type: 'checkbox' });
  view.append(el('div', { class: 'card' }, el('h2', {}, 'Nouvelle classe'), el('div', { class: 'grid' }, el('div', {}, el('label', {}, 'Nom'), nom), el('div', {}, el('label', {}, 'Classe précédente directe'), prev)),
    el('div', { class: 'checks' }, el('label', {}, ex, 'A examen'), el('label', {}, so, 'Spécialité obligatoire')),
    el('div', { class: 'row', style: 'margin-top:.6rem' }, el('button', { class: 'primary', onclick: async () => {
      const r = await api('POST', '/classes', { nom: nom.value, classePrecedenteId: prev.value || null, aExamen: ex.checked, specialiteObligatoire: so.checked }); r.ok ? nav() : err(r); } }, 'Ajouter'))));
  view.append(el('div', { class: 'card' }, el('table', { class: 't' },
    el('tr', {}, ['Classe', 'Précédente', 'Arborescence', 'Examen', 'Spéc. oblig.', ''].map(h => el('th', {}, h))),
    cs.map(c => el('tr', {}, el('td', {}, c.nom), el('td', {}, (cs.find(x => x.id === c.classePrecedenteId) || {}).nom || '—'), el('td', {}, c.arborescence.join(' ← ') || '—'),
      el('td', {}, c.aExamen ? 'Oui' : 'Non'), el('td', {}, c.specialiteObligatoire ? 'Oui' : 'Non'),
      el('td', {}, el('button', { onclick: async () => {
        const n = el('input', { type: 'text', value: c.nom }), p = el('select', {}, el('option', { value: '' }, 'Aucune'), cs.filter(x => x.id !== c.id).map(x => el('option', { value: x.id, ...(x.id === c.classePrecedenteId ? { selected: true } : {}) }, x.nom)));
        const e1 = el('input', { type: 'checkbox', checked: c.aExamen }), s1 = el('input', { type: 'checkbox', checked: c.specialiteObligatoire });
        if (await ask('Modifier la classe', b => b.append(n, p, el('label', {}, e1, ' A examen'), el('label', {}, s1, ' Spécialité obligatoire')))) {
          const r = await api('PUT', '/classes/' + c.id, { nom: n.value, classePrecedenteId: p.value || null, aExamen: e1.checked, specialiteObligatoire: s1.checked }); r.ok ? nav() : err(r); } } }, 'Modifier'), ' ',
        el('button', { class: 'danger', onclick: async () => { if (await supprimer('/classes/' + c.id, c.nom, cs.filter(x => x.id !== c.id), false)) nav(); } }, 'Supprimer')))))));
}


// Barre d'outils : insère des modèles de formules / structures / images à la position du curseur
function insertAt(ta, texte, selDebut, selFin) {
  const a = ta.selectionStart, b = ta.selectionEnd;
  ta.value = ta.value.slice(0, a) + texte + ta.value.slice(b);
  ta.focus();
  ta.setSelectionRange(a + (selDebut ?? texte.length), a + (selFin ?? texte.length));
  ta.dispatchEvent(new Event('input'));                    // met à jour l'aperçu
}
const OUTILS = [['u₁', 'Indice', '$u_{1}$', 3, 4], ['x²', 'Exposant', '$x^{2}$', 4, 5], ['a⁄b', 'Fraction', '$\\frac{a}{b}$', 8, 9], ['√', 'Racine carrée', '$\\sqrt{x}$', 8, 9],
  ['ℝ', 'Ensemble des réels', '$\\R$'], ['H₂O', 'Formule chimique', '$\\ce{H2O}$', 5, 8], ['⇌', 'Équation chimique', '$\\ce{A + B -> C}$', 5, 15],
  ['CH₃–', 'Formule semi-développée', '$\\ce{CH3-CH2-OH}$', 5, 17], [':Ö:', 'Doublets de Lewis', '$\\lTB{O}$', 6, 7],
  ['⌬', 'Structure chimique (topologique, développée ou Cram)', '\n```mol topologique\nCCO éthanol\n```\n', 22, 25]];
function barreOutils(ta) {
  const file = el('input', { type: 'file', accept: 'image/png,image/jpeg,image/gif,image/webp,image/svg+xml', style: 'display:none' });
  file.addEventListener('change', async () => {
    const f = file.files[0]; if (!f) return;
    const r = await fetch('/api/admin/media', { method: 'POST', headers: { 'X-Admin-Token': TOKEN, 'Content-Type': f.type || 'application/octet-stream', 'X-Filename': encodeURIComponent(f.name) }, body: f });
    const d = await r.json().catch(() => ({}));
    file.value = '';
    if (r.ok) {
      // curseur à l'intérieur d'un bloc ```…``` : on insère l'image après la fermeture du bloc (sinon elle casserait le bloc)
      let pos = ta.selectionStart;
      if ((ta.value.slice(0, pos).match(/```/g) || []).length % 2 === 1) {
        const fin = ta.value.indexOf('```', pos);
        if (fin >= 0) { const nl = ta.value.indexOf('\n', fin); pos = nl >= 0 ? nl + 1 : ta.value.length; }
      }
      ta.setSelectionRange(pos, pos);
      insertAt(ta, '\n' + d.markdown + '\n');
    } else err({ data: d, status: r.status });
  });
  return el('div', { class: 'row outils' }, OUTILS.map(([lib, titre, txt, a, b]) => el('button', { type: 'button', title: titre, onclick: () => insertAt(ta, txt, a, b) }, lib)),
    el('button', { type: 'button', title: 'Insérer une image (schéma de Newman, Fischer, figure…)', onclick: () => file.click() }, '🖼'), file);
}

// Aperçu fidèle (même rendu Markdown que les épreuves, formules mises en forme par KaTeX)
function preview(ta) {
  const box = el('div', { class: 'md preview' });
  let timer, seq = 0;
  const upd = () => { clearTimeout(timer); timer = setTimeout(async () => {
    const my = ++seq; const r = await api('POST', '/preview', { markdown: ta.value });
    if (my !== seq || !r.ok) return;
    box.innerHTML = r.data.html; renderMath(box);       // HTML produit par le serveur (HTML brut désactivé)
    setTimeout(() => {
      const w = [...r.data.avertissements, ...[...box.querySelectorAll('.katex-error')].map(x => 'Formule invalide : ' + x.textContent.slice(0, 60))];
      box.querySelectorAll('.avert').forEach(x => x.remove());
      if (w.length) box.prepend(el('div', { class: 'avert mol-error' }, '⚠ ', w.join(' · ')));
    }, 150);
  }, 300); };
  ta.addEventListener('input', upd); upd();
  return box;
}
const AIDE = [['Indice', 'u_1'], ['Indice composé', 'u_{n+1}'], ['Exposant', 'x^2'], ['Exponentielle', '\\mathrm{e}^{2x}'], ['Puissance de 10', '10^{-4}'],
  ['Fraction', '\\frac{a}{b}'], ['Racine', '\\sqrt{14}'], ['Ensemble des réels', '\\R'], ['Intervalle', '[0\\,;\\,+\\infty['], ['Vecteur', '\\overrightarrow{AB}'],
  ['Formule chimique', '\\ce{H2O}'], ['Semi-développée', '\\ce{CH3-CH(OH)-CH3}'], ['Doublets de Lewis', '\\mathrm{H}-\\lTB{O}-\\mathrm{H}'], ['Ion', '\\ce{SO4^2-}'], ['Équation-bilan', '\\ce{CH4 + 2O2 -> CO2 + 2H2O}'], ['Unité', '\\pu{m.s-1}']];
function aide() {
  const d = el('details', {}, el('summary', {}, 'Aide : écrire des formules (indices, exposants, chimie…)'),
    el('p', { class: 'mut' }, 'Une formule s\'écrit entre dollars : $u_1$ dans une phrase, $$…$$ pour une formule centrée sur sa ligne. Pour dessiner une molécule : bloc ```mol topologique|developpee|cram (un SMILES par ligne, légende facultative après un espace). Schémas de Newman/Fischer ou figures : bouton 🖼.'),
    el('table', { class: 'aide' }, AIDE.map(([nom, tex]) => el('tr', {}, el('td', {}, nom), el('td', {}, el('code', {}, '$' + tex + '$')), el('td', {}, el('span', { class: 'math inline' }, tex))))));
  renderMath(d);
  return d;
}
async function tExercices(view) {
  const [ms, ps, cs, ss] = await Promise.all(['matieres', 'parties', 'classes', 'specialites'].map(async k => (await api('GET', '/' + k)).data));
  const f = { q: el('input', { type: 'text', placeholder: 'Recherche texte' }), m: el('select', {}, el('option', { value: '' }, 'Matière'), ms.map(x => el('option', { value: x.id }, x.nom))),
    p: el('select', {}, el('option', { value: '' }, 'Partie'), ps.map(x => el('option', { value: x.id }, (ms.find(m => m.id === x.matiereId) || {}).nom + ' › ' + x.nom))),
    c: el('select', {}, el('option', { value: '' }, 'Classe'), cs.map(x => el('option', { value: x.id }, x.nom))),
    s: el('select', {}, el('option', { value: '' }, 'Séquence'), el('option', { value: 'vide' }, 'Session vide'), SEQ.slice(1).map(n => el('option', { value: n }, 'Séquence ' + n))) };
  const list = el('div', {}), editor = el('div', {});
  let seq = 0;               // une réponse périmée (arrivée après une plus récente) est ignorée
  const load = async () => {
    const my = ++seq;
    const q = new URLSearchParams({ limit: 100 }); if (f.q.value) q.set('q', f.q.value); if (f.m.value) q.set('matiereId', f.m.value); if (f.p.value) q.set('partieId', f.p.value); if (f.c.value) q.set('classeId', f.c.value); if (f.s.value) q.set('session', f.s.value);
    const { data } = await api('GET', '/exercices?' + q);
    if (my !== seq) return;
    list.replaceChildren(el('p', { class: 'mut' }, data.total + ' exercice(s)'), el('table', { class: 't' }, data.items.map(e => el('tr', {},
      el('td', {}, e.sujet.slice(0, 90)), el('td', {}, e.session ? 'S' + e.session : 'vide', e.tagExamen ? ' · Examen' : ''), el('td', {}, e.niveauIntrinseque),
      el('td', {}, el('button', { onclick: () => edit(e) }, 'Éditer'), ' ', el('button', { class: 'danger', onclick: async () => { if (confirm('Supprimer cet exercice ?')) { const r = await api('DELETE', '/exercices/' + e.id); r.ok ? load() : err(r); } } }, 'Supprimer'))))));
  };
  function edit(e) {
    e = e || { sujet: '', corrige: '', affectations: [], classeIds: [], specialiteIds: ['SPECIAL:Aucune'], session: null, niveauIntrinseque: 'Moyen', tagExamen: false };
    const sujet = el('textarea', { value: e.sujet }), corrige = el('textarea', { value: e.corrige });
    const sess = el('select', {}, SEQ.map(n => el('option', { value: n, ...(String(n) === String(e.session ?? '') ? { selected: true } : {}) }, n === '' ? 'Vide (hors séquence)' : 'Séquence ' + n)));
    const niv = el('select', {}, ['Facile', 'Moyen', 'Difficile'].map(n => el('option', { value: n, ...(n === e.niveauIntrinseque ? { selected: true } : {}) }, n)));
    const tag = el('input', { type: 'checkbox', checked: e.tagExamen });
    const syncTag = () => { tag.disabled = sess.value === ''; if (tag.disabled) tag.checked = false; }; sess.addEventListener('change', syncTag); syncTag();   // tag grisé si session vide
    const mChecks = ms.map(m => { const cur = e.affectations.find(a => a.matiereId === m.id);
      const cb = el('input', { type: 'checkbox', checked: !!cur }); const mp = ps.filter(p => p.matiereId === m.id);
      const sel = el('select', {}, mp.length ? mp.map(p => el('option', { value: p.id, ...(cur && cur.partieId === p.id ? { selected: true } : {}) }, p.nom)) : el('option', { value: '' }, '(aucune partie : à créer d\'abord)'));
      return { m, cb, sel, node: el('div', { class: 'row' }, el('label', {}, cb, ' ', m.nom), sel) }; });
    const cChecks = cs.map(c => ({ c, cb: el('input', { type: 'checkbox', checked: e.classeIds.includes(c.id) }) }));
    const sChecks = [{ id: 'SPECIAL:Aucune', nom: 'Aucune (universel)' }, ...ss].map(s => ({ s, cb: el('input', { type: 'checkbox', checked: e.specialiteIds.includes(s.id) }) }));
    editor.replaceChildren(el('div', { class: 'card' }, el('h2', {}, e.id ? 'Modifier l\'exercice' : 'Nouvel exercice'),
      aide(), el('label', {}, 'Sujet (Markdown + formules)'), barreOutils(sujet), sujet, preview(sujet), el('label', {}, 'Corrigé (Markdown + formules)'), barreOutils(corrige), corrige, preview(corrige),
      el('label', {}, 'Matières et partie associée'), mChecks.map(x => x.node),
      el('label', {}, 'Classes'), el('div', { class: 'checks' }, cChecks.map(x => el('label', {}, x.cb, x.c.nom))),
      el('label', {}, 'Spécialités'), el('div', { class: 'checks' }, sChecks.map(x => el('label', {}, x.cb, x.s.nom))),
      el('div', { class: 'grid' }, el('div', {}, el('label', {}, 'Session'), sess), el('div', {}, el('label', {}, 'Niveau intrinsèque'), niv)),
      el('label', {}, tag, ' Tag Examen (séquences 1 à 6 uniquement)'),
      el('div', { class: 'row', style: 'margin-top:.8rem' }, el('button', { class: 'primary', onclick: async () => {
        const sans = mChecks.find(x => x.cb.checked && !x.sel.value);
        if (sans) { alert(`Créez d'abord une partie pour la matière « ${sans.m.nom} » (onglet Matières & parties).`); return; }
        const body = { sujet: sujet.value, corrige: corrige.value, session: sess.value === '' ? null : Number(sess.value), niveauIntrinseque: niv.value, tagExamen: tag.checked,
          affectations: mChecks.filter(x => x.cb.checked).map(x => ({ matiereId: x.m.id, partieId: x.sel.value })), classeIds: cChecks.filter(x => x.cb.checked).map(x => x.c.id),
          specialiteIds: sChecks.filter(x => x.cb.checked).map(x => x.s.id) };
        const r = e.id ? await api('PUT', '/exercices/' + e.id, body) : await api('POST', '/exercices', body);
        if (r.ok) { editor.replaceChildren(); load(); } else err(r); } }, 'Enregistrer'), el('button', { onclick: () => editor.replaceChildren() }, 'Fermer'))));
    editor.scrollIntoView({ behavior: 'smooth' });
  }
  let timer; f.q.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(load, 250); });   // pas une requête par frappe
  for (const k of Object.keys(f)) if (k !== 'q') f[k].addEventListener('change', load);
  view.append(el('div', { class: 'card' }, el('div', { class: 'row' }, Object.values(f), el('button', { class: 'primary', onclick: () => edit() }, '+ Nouvel exercice'))), editor, el('div', { class: 'card' }, list));
  load();
}
async function tMedias(view) {
  const ms = (await api('GET', '/media')).data;
  view.append(el('div', { class: 'card' }, el('h2', {}, 'Images des énoncés'),
    el('p', { class: 'mut' }, 'Téléversez les images depuis l\'éditeur d\'exercice (bouton 🖼). PNG, JPEG, GIF, WebP ou SVG, 2 Mo maximum. Le contenu est contrôlé (un SVG avec script est refusé).'),
    ms.length ? el('table', { class: 't' }, ms.map(m => el('tr', {}, el('td', {}, el('img', { src: m.url, alt: m.nom, style: 'max-width:90px;max-height:60px;background:#fff' })), el('td', {}, m.nom), el('td', {}, Math.round(m.taille / 1024) + ' Ko'),
      el('td', {}, m.utilisations + ' exercice(s)'), el('td', {}, el('button', { onclick: () => navigator.clipboard && navigator.clipboard.writeText('![' + m.nom.replace(/\.[^.]+$/, '') + '](' + m.url + ')') }, 'Copier le Markdown'), ' ',
        el('button', { class: 'danger', onclick: async () => { if (!confirm('Supprimer cette image ?')) return; let r = await api('DELETE', '/media/' + m.id);
          if (r.status === 409 && confirm('Image utilisée par ' + r.data.count + ' exercice(s). Supprimer quand même ?')) r = await api('DELETE', '/media/' + m.id + '?force=1');
          r.ok ? nav() : err(r); } }, 'Supprimer'))))) : el('p', { class: 'mut' }, 'Aucune image.')));
}
async function tIO(view) {
  const mode = el('select', {}, el('option', { value: 'fusionner' }, 'Fusionner (mise à jour par id, ajout des nouveaux)'), el('option', { value: 'remplacer' }, 'Remplacer toute la banque'));
  const file = el('input', { type: 'file', accept: '.json,application/json' }), out = el('pre', { class: 'j' });
  view.append(el('div', { class: 'card' }, el('h2', {}, 'Export'), el('button', { class: 'primary', onclick: async () => {
      const r = await fetch('/api/admin/export', { headers: { 'X-Admin-Token': TOKEN } }); const b = await r.blob();
      const a = el('a', { href: URL.createObjectURL(b), download: 'banque.json' }); a.click(); } }, 'Télécharger banque.json')),
    el('div', { class: 'card' }, el('h2', {}, 'Import (schéma 1.1)'), mode, el('div', { class: 'row', style: 'margin-top:.6rem' }, file, el('button', { class: 'primary', onclick: async () => {
      if (!file.files[0]) return; if (mode.value === 'remplacer' && !confirm('Remplacer TOUTE la banque ?')) return;
      let doc; try { doc = JSON.parse(await file.files[0].text()); } catch { out.textContent = 'JSON illisible'; return; }
      const r = await api('POST', '/import?mode=' + mode.value, doc); out.textContent = r.ok ? 'Import réussi : ' + JSON.stringify(r.data) : (r.data.message + '\n- ' + (r.data.errors || []).join('\n- ')); } }, 'Importer')), out));
}
async function tJournal(view) {
  const types = ['', 'GENERATION', 'RULE_50_RELAXED', 'UNIQUENESS_SATURATED', 'INCOMPLETE_EXAM', 'INFO_HISTORY_PURGED'];
  const sel = el('select', {}, types.map(t => el('option', { value: t }, t || 'Tous les types'))), box = el('div', {});
  let seq = 0;
  const load = async () => { const my = ++seq; const { data } = await api('GET', '/journal?limit=200' + (sel.value ? '&type=' + sel.value : '')); if (my !== seq) return;
    box.replaceChildren(el('p', { class: 'mut' }, data.total + ' entrée(s) — journal réservé à l\'administration'), el('table', { class: 't' },
      el('tr', {}, ['Date', 'Utilisateur', 'Type', 'Paramètres', 'Détails'].map(h => el('th', {}, h))),
      data.items.map(j => el('tr', {}, el('td', {}, j.timestamp.replace('T', ' ').slice(0, 19)), el('td', {}, j.userId.slice(0, 8)), el('td', {}, j.type),
        el('td', {}, el('pre', { class: 'j' }, JSON.stringify(j.params))), el('td', {}, el('pre', { class: 'j' }, JSON.stringify(j.details))))))); };
  sel.addEventListener('change', load); view.append(el('div', { class: 'card' }, sel), el('div', { class: 'card' }, box)); load();
}
async function tReglages(view) {
  const r = (await api('GET', '/reglages')).data, inp = el('input', { type: 'number', min: 1, value: r.retentionJours ?? '', placeholder: 'vide = conservation illimitée' }), out = el('p', { class: 'mut' });
  view.append(el('div', { class: 'card' }, el('h2', {}, 'Conservation de l\'historique d\'unicité'), el('label', {}, 'retentionJours'), inp,
    el('p', { class: 'mut' }, 'La purge s\'applique par utilisateur et ne supprime jamais sa dernière génération. Exécutée au démarrage puis toutes les 24 h.'),
    el('div', { class: 'row' }, el('button', { class: 'primary', onclick: async () => { const x = await api('PUT', '/reglages', { retentionJours: inp.value ? Number(inp.value) : null }); out.textContent = x.ok ? 'Enregistré.' : 'Valeur invalide.'; } }, 'Enregistrer'),
      el('button', { onclick: async () => { const x = await api('POST', '/purge'); out.textContent = x.ok ? x.data.supprimes + ' génération(s) supprimée(s).' : 'Erreur.'; } }, 'Purger maintenant')), out));
}
nav();
