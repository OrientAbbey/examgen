import chromium from '@sparticuz/chromium';
import puppeteer from 'puppeteer-core';
import fs from 'fs';
import os from 'os'; import path from 'path';
const BASE = process.env.BASE || 'http://localhost:8770', OUT = process.env.OUT || path.resolve('out'), TOKEN = process.env.EXAMGEN_ADMIN_TOKEN || 'demo', TMP = os.tmpdir();
fs.mkdirSync(OUT, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const results = [], problems = []; let step = '';
const ok = (name, cond, extra = '') => { step = name; results.push([cond ? 'OK ' : 'KO ', name, extra]); if (!cond) problems.push(name); };
const browser = await puppeteer.launch({ args: [...chromium.args, '--no-sandbox'], executablePath: await chromium.executablePath(), headless: 'shell', defaultViewport: { width: 1100, height: 900 } });
const page = await browser.newPage();
const errors = [], alerts = [], badreq = [];
page.on('response', async r => { if (r.status() >= 400 && r.request().method() !== 'GET' && !/\/api\/generate/.test(r.url())) badreq.push(r.status() + ' ' + r.request().method() + ' ' + r.url().replace(BASE, '') + ' ' + (r.request().postData() || '').slice(0, 300)); });
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errors.push('console: ' + m.text()); });
page.on('dialog', async d => { if (d.type() !== 'confirm') alerts.push(d.message()); await d.accept(); });
const shot = async (n, full = true) => page.screenshot({ path: `${OUT}/${n}.png`, fullPage: full });
const clickText = async (sel, text) => { const h = await page.evaluateHandle((s, t) => [...document.querySelectorAll(s)].find(e => e.textContent.trim() === t), sel, text); if (!h.asElement()) throw new Error('introuvable: ' + text); await h.asElement().click(); };

try {
// ───────── Module utilisateur ─────────
await page.goto(BASE + '/'); await page.waitForSelector('#matiere option:nth-child(2)');
ok('U1 bouton Générer inactif au départ', await page.$eval('#generer', b => b.disabled));
await shot('01-accueil');
await page.select('#matiere', await page.$eval('#matiere option:nth-child(2)', o => o.value));
const ter = await page.evaluate(() => [...document.querySelectorAll('#classe option')].find(o => o.textContent === 'Terminale').value);
await page.select('#classe', ter);
await clickText('#difficulte label', 'Moyen');
ok('U2 spécialité obligatoire : bouton inactif sans spécialité', await page.$eval('#generer', b => b.disabled));
ok('U3 astérisque spécialité affiché', (await page.$eval('#spec-req', e => e.textContent)) === '*');
ok('U4 aucun message affiché', (await page.$eval('#statut', e => e.textContent)) === '');
await page.select('#specialite', await page.$eval('#specialite option:nth-child(2)', o => o.value));
await page.select('#session', '3');
ok('U5 bouton actif une fois le formulaire valide', !(await page.$eval('#generer', b => b.disabled)));
await shot('02-formulaire-rempli', false);
await page.click('#generer'); await page.waitForSelector('#epreuve:not([hidden]) .exo');
const n1 = await page.$$eval('#exos .exo', e => e.length), t1 = await page.$eval('#exos', e => e.innerText);
ok('U6 épreuve générée (Moyen = 4 exercices)', n1 === 4, `n=${n1}`);
ok('U7 numérotation Exercice 1..4', (await page.$$eval('#exos h3', h => h.map(x => x.textContent).join('|'))) === 'Exercice 1|Exercice 2|Exercice 3|Exercice 4');
ok('U8 le sujet ne contient pas de corrigé', !/Solution/.test(t1));
const enonces = await page.$$eval('#exos .exo', xs => xs.map(x => ({ t: x.innerText, questions: x.querySelectorAll('li').length })));
ok('U7b chaque exercice est un vrai énoncé (consigne + liste de questions)', enonces.every(e => e.questions >= 1 && /(Calculer|Résoudre|Déterminer|Démontrer|Montrer|Développer|Dresser|Justifier|Combien|Exprimer|Donner|Étudier|Factoriser|Comparer)/.test(e.t)) && !/démonstration|lorem|#\d+/i.test(enonces.map(e => e.t).join(' ')), enonces.map(e => e.questions).join('/'));
const rend = await page.evaluate(() => { const c = document.querySelector('#exos').cloneNode(true); c.querySelectorAll('.katex-mathml').forEach(x => x.remove());
  return { katex: document.querySelectorAll('#exos .katex').length, sub: document.querySelectorAll('#exos .msupsub').length, err: document.querySelectorAll('#exos .katex-error').length,
    brut: /\$|\\(frac|mathrm|ce|pu|vec|sqrt|binom|ln|lim|text)|[_^]\{|\^[0-9a-z]|_[0-9a-z]/i.test(c.textContent) }; });
ok('U7c formules mises en forme par KaTeX (indices/exposants), aucun LaTeX brut visible', rend.katex >= 5 && rend.sub >= 2 && rend.err === 0 && !rend.brut, JSON.stringify(rend));
const themes = await page.evaluate(() => document.querySelectorAll('#exos .exo').length);
await shot('03-epreuve-generee');
await page.click('#regenerer'); await sleep(900);
const t2 = await page.$eval('#exos', e => e.innerText);
ok('U9 Régénérer produit une autre épreuve (unicité)', t2 !== t1 && (await page.$$eval('#exos .exo', e => e.length)) === 4);
// pages imprimable / corrigé (nouvel onglet)
const [popup] = await Promise.all([new Promise(r => browser.once('targetcreated', t => r(t.page()))), page.click('#corrige')]);
await popup.waitForSelector('.exo'); const ctext = await popup.$eval('body', b => b.innerText);
ok('U10 corrigé dans un onglet séparé, même nombre d\'exercices', (await popup.$$eval('.exo', e => e.length)) === 4 && /Solution :/.test(ctext) && /^Corrigé — /.test(await popup.title()));
await popup.setViewport({ width: 900, height: 800 }); await popup.screenshot({ path: `${OUT}/04-corrige.png`, fullPage: true });
const sujetUrl = popup.url().replace('/corrige', '');
await popup.close();
const pp = await browser.newPage(); await pp.evaluateOnNewDocument(() => { window.print = () => { window.__printed = true; }; });
await pp.goto(sujetUrl + '?print=1'); await pp.waitForSelector('.exo'); await sleep(300);
ok('U11 version imprimable : formules rendues, impression déclenchée, sans corrigé', (await pp.$$eval('.katex', x => x.length)) >= 5 && (await pp.evaluate(() => window.__printed === true)) && !/Solution/.test(await pp.$eval('body', b => b.innerText)));
await pp.pdf({ path: `${OUT}/epreuve-imprimable.pdf`, format: 'A4', printBackground: true }); await pp.close();
// mobile
const mob = await browser.newPage(); await mob.setViewport({ width: 390, height: 800, isMobile: true });
await mob.goto(BASE + '/'); await mob.waitForSelector('#matiere'); await mob.screenshot({ path: `${OUT}/05-mobile.png` });
ok('U12 mobile : pas de défilement horizontal', await mob.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)); await mob.close();

// ───────── Physique-Chimie : formules moléculaires, ions, unités ─────────
await page.goto(BASE + '/'); await page.waitForSelector('#matiere option:nth-child(3)');
await page.select('#matiere', await page.evaluate(() => [...document.querySelectorAll('#matiere option')].find(o => o.textContent === 'Physique-Chimie').value));
await page.select('#classe', await page.evaluate(() => [...document.querySelectorAll('#classe option')].find(o => o.textContent === 'Seconde').value));
await page.select('#session', '1'); await clickText('#difficulte label', 'Facile'); await page.click('#generer');
await page.waitForSelector('#epreuve:not([hidden]) .exo .katex');
const chim = await page.evaluate(() => { const c = document.querySelector('#exos').cloneNode(true); c.querySelectorAll('.katex-mathml').forEach(x => x.remove());
  const ce = [...document.querySelectorAll('#exos .katex-html')].map(x => x.textContent).join(' ');
  return { exo: document.querySelectorAll('#exos .exo').length, sub: document.querySelectorAll('#exos .msupsub').length, err: document.querySelectorAll('#exos .katex-error').length,
    mol: /mol/.test(ce), brut: /\$|\\(ce|pu|frac)|[_^]\{/.test(c.textContent) }; });
ok('C1 épreuve de Physique-Chimie : formules moléculaires et unités rendues (H₂O, mol·g⁻¹…)', chim.exo === 2 && chim.sub >= 3 && chim.mol && chim.err === 0 && !chim.brut, JSON.stringify(chim));
await shot('03b-epreuve-chimie');
const [popup2] = await Promise.all([new Promise(r => browser.once('targetcreated', t => r(t.page()))), page.click('#corrige')]);
await popup2.setViewport({ width: 900, height: 700 }); await popup2.waitForSelector('.exo .katex'); await sleep(300);
ok('C2 corrigé de Physique-Chimie rendu (calculs avec unités)', (await popup2.$$eval('.katex', x => x.length)) >= 4 && (await popup2.$$eval('.katex-error', x => x.length)) === 0);
await popup2.screenshot({ path: `${OUT}/04b-corrige-chimie.png`, fullPage: true }); await popup2.close();

// ───────── Module administrateur ─────────
await page.goto(BASE + '/admin'); await page.waitForSelector('#dlg[open] input[type=password]');
await shot('06-admin-connexion', false);
await page.type('#dlg input', 'faux'); await page.keyboard.press('Enter'); await sleep(700);
ok('A1 mauvais jeton : nouvelle demande de connexion', await page.$('#dlg[open] input[type=password]') !== null);
await page.type('#dlg input', TOKEN); await page.keyboard.press('Enter');
await page.waitForSelector('.card strong'); await sleep(300);
ok('A2 connexion avec le bon jeton : matières affichées', (await page.$$eval('.card strong', e => e.map(x => x.textContent))).includes('Mathématiques'));
await shot('07-admin-matieres');
// ajout matière + partie
await page.type('.card input[placeholder="Nouvelle matière"]', 'Physique'); await clickText('.card button', 'Ajouter'); await sleep(700);
ok('A3 création d\'une matière', (await page.$$eval('.card strong', e => e.map(x => x.textContent))).includes('Physique'));
// classes
await clickText('#tabs button', 'Classes'); await sleep(600);
ok('A4 arborescence des classes affichée', /Première ← Seconde/.test(await page.$eval('table.t', t => t.innerText)));
await shot('08-admin-classes');
// exercices : création via l'éditeur
await clickText('#tabs button', 'Exercices'); await sleep(800);
await shot('09-admin-exercices');
await clickText('button', '+ Nouvel exercice'); await page.waitForSelector('#view textarea'); await sleep(900);
const [ta1, ta2] = await page.$$('#view textarea'); await ta1.type('Sujet UI-TEST **gras**, avec $u_1$, $\\mathrm{e}^{2}$, $\\ce{H2O}$ et $\\ce{SO4^2-}$ ; $x^2 + \\frac{1}{2}$.'); await ta2.type('Corrigé UI-TEST');
ok('A5 tag Examen grisé quand la session est vide', await page.evaluate(() => { const l = [...document.querySelectorAll('label')].find(x => x.textContent.includes('Tag Examen')); return l.querySelector('input').disabled; }));
const mathsCb = await page.evaluateHandle(() => [...document.querySelectorAll('.row label')].find(l => l.textContent.trim() === 'Mathématiques').querySelector('input'));
await mathsCb.asElement().click();
const terCb = await page.evaluateHandle(() => [...document.querySelectorAll('.checks label')].find(l => l.textContent.trim() === 'Terminale').querySelector('input'));
await terCb.asElement().click();
const sessSel = (await page.$$('#view select')).at(-2); await sessSel.select('2');
ok('A6 tag Examen dégrisé pour une session 1-6', await page.evaluate(() => !([...document.querySelectorAll('label')].find(x => x.textContent.includes('Tag Examen')).querySelector('input').disabled)));
await page.waitForFunction(() => document.querySelectorAll('#view .preview .katex').length >= 5, { timeout: 8000 }).catch(() => {});
const pv = await page.evaluate(() => { const p = document.querySelector('#view .preview'); const c = p.cloneNode(true); c.querySelectorAll('.katex-mathml').forEach(x => x.remove());
  return { katex: p.querySelectorAll('.katex').length, sub: p.querySelectorAll('.msupsub').length, err: p.querySelectorAll('.katex-error').length, brut: /\$|\\|[_^]\{|\^2|_1/.test(c.textContent), gras: !!p.querySelector('strong'),
    aide: document.querySelectorAll('#view table.aide .katex').length }; });
ok('A5b éditeur : aperçu en direct (u₁, e², H₂O, SO₄²⁻, fraction) et aide-mémoire rendus', pv.katex >= 5 && pv.sub >= 4 && pv.err === 0 && !pv.brut && pv.gras && pv.aide >= 14, JSON.stringify(pv));
await shot('10-admin-editeur', false);
await clickText('button', 'Enregistrer'); await page.waitForFunction(() => !document.querySelector('#view textarea'), { timeout: 8000 });
await page.type('input[placeholder="Recherche texte"]', 'UI-TEST'); await sleep(500); await page.waitForFunction(() => /1 exercice\(s\)/.test(document.querySelector('#view').innerText), { timeout: 8000 }).catch(() => {});
ok('A7 exercice créé et retrouvé par la recherche', /1 exercice\(s\)/.test(await page.$eval('#view', v => v.innerText)));
// validation serveur : exercice sans classe → refus lisible
await clickText('button', 'Éditer'); await page.waitForSelector('#view textarea'); await sleep(900);
const t2cb = await page.evaluateHandle(() => [...document.querySelectorAll('.checks label')].find(l => l.textContent.trim() === 'Terminale').querySelector('input'));
await t2cb.asElement().click(); alerts.length = 0; await clickText('button', 'Enregistrer'); await sleep(700);
ok('A8 enregistrement invalide refusé avec message lisible', alerts.length === 1 && /classeIds/.test(alerts[0]), alerts.join(' / '));
// suppression avec réaffectation (spécialité référencée)
await clickText('#tabs button', 'Spécialités'); await sleep(600);
const before = await page.$$eval('table.t tr', r => r.length);
const delSVT = () => page.evaluate(() => [...document.querySelectorAll('table.t tr')].find(r => r.innerText.includes('Physique-Chimie')).querySelector('button.danger').click());
await delSVT(); await page.waitForSelector('#dlg[open] select'); await shot('11-admin-reaffectation', false);
await page.keyboard.press('Escape'); await sleep(600);
ok('A9 Échap annule la réaffectation (rien supprimé)', (await page.$$eval('table.t tr', r => r.length)) === before);
await delSVT(); await page.waitForSelector('#dlg[open] select'); await page.click('#dlg button[value=ok]');
await page.waitForFunction(n => document.querySelectorAll('table.t tr').length === n, { timeout: 8000 }, before - 1).catch(() => {});
ok('A10 suppression bloquée (référencée) puis réaffectation validée', (await page.$$eval('table.t tr', r => r.length)) === before - 1);
alerts.length = 0;
await page.evaluate(() => [...document.querySelectorAll('table.t tr')].find(r => r.innerText.includes('Mathématiques')).querySelector('button.danger').click()); await sleep(900);
ok('A10b dernière cible : message clair, rien supprimé', alerts.some(a => /aucune cible/.test(a)) && (await page.$$eval('table.t tr', r => r.length)) === before - 1);
// import fusion
await clickText('#tabs button', 'Import / Export'); await sleep(400);
const inp = await page.$('input[type=file]'); fs.writeFileSync(path.join(TMP, 'export.json'), await (await fetch(BASE + '/api/admin/export', { headers: { 'X-Admin-Token': TOKEN } })).text());
await inp.uploadFile(path.join(TMP, 'export.json'));
await clickText('button', 'Importer'); await sleep(1200);
ok('A11 import (fusion) réussi', /Import réussi/.test(await page.$eval('pre.j', p => p.textContent)));
await shot('12-admin-import', false);
fs.writeFileSync(path.join(TMP, 'bad.json'), '{"schemaVersion":"1.1","matieres":[],"parties":[],"classes":[],"specialites":[],"exercices":[{"id":"x"}]}');
await (await page.$('input[type=file]')).uploadFile(path.join(TMP, 'bad.json')); await clickText('button', 'Importer'); await sleep(800);
ok('A12 import invalide : erreurs listées, rien modifié', /Fichier invalide/.test(await page.$eval('pre.j', p => p.textContent)));
// journal + réglages
await clickText('#tabs button', 'Journal'); await sleep(900);
ok('A13 journal : générations visibles', /GENERATION/.test(await page.$eval('#view', v => v.innerText)));
await shot('13-admin-journal');
await clickText('#tabs button', 'Réglages'); await sleep(400);
await page.type('input[type=number]', '30'); await clickText('button', 'Enregistrer'); await sleep(500);
ok('A14 réglage de rétention enregistré', /Enregistré/.test(await page.$eval('#view', v => v.innerText)));
await clickText('button', 'Purger maintenant'); await sleep(600);
ok('A15 purge manuelle', /supprimée/.test(await page.$eval('#view', v => v.innerText)));
ok('Z  aucune erreur JavaScript', errors.length === 0, errors.join(' | '));
} catch (e) { console.log('EXCEPTION:', e.message, '| après:', step, '| ALERTS:', JSON.stringify(alerts), '| ERRORS:', JSON.stringify(errors), '| BADREQ:', JSON.stringify(badreq)); try { console.log('VIEW:', (await page.$eval('#view', v => v.innerText)).slice(0, 400)); console.log('DIALOG OPEN:', await page.$eval('#dlg', d => d.open)); await page.screenshot({ path: path.join(OUT, 'echec.png') }); } catch {} problems.push('exception'); }
await browser.close();
console.log(results.map(r => r.join(' ')).join('\n')); console.log(problems.length ? '\nÉCHECS: ' + problems.join(', ') : '\nTOUT OK (' + results.length + ' vérifications)');
