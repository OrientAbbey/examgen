/* Rendu des formules et des structures chimiques.
   - Formules : le serveur produit <span class="math inline">LaTeX</span> (ou <div class="math block">) ; KaTeX (+ mhchem :
     \\ce{H2O}, \\pu{m.s-1}) les met en forme dans le navigateur, écran comme impression.
   - Structures : le serveur produit <figure class="mol" data-smiles=… data-style=…> ; SmilesDrawer (chargé seulement si nécessaire)
     les dessine en SVG noir et blanc (topologique, développée, Cram). */
(function () {
  var SIZES = { petit: [220, 150], moyen: [300, 200], grand: [440, 280] };
  var NOIR = { C: '#000', O: '#000', N: '#000', F: '#000', CL: '#000', BR: '#000', I: '#000', P: '#000', S: '#000', B: '#000', SI: '#000', H: '#000', BACKGROUND: '#fff' };
  var waiting = null;

  function loadChem(cb) {
    if (window.SmilesDrawer) return cb();
    if (!waiting) {
      waiting = [];
      var s = document.createElement('script');
      s.src = '/static/chem/smiles-drawer.min.js';
      s.onload = function () { var w = waiting; waiting = null; w.forEach(function (f) { f(); }); };
      s.onerror = function () { waiting = null; };
      document.head.appendChild(s);
    }
    waiting.push(cb);
  }

  function fail(fig, svg, err) {
    if (svg && svg.parentNode) svg.parentNode.removeChild(svg);
    fig.classList.add('mol-error', 'rendered');
    var sp = document.createElement('span'); sp.textContent = 'Structure non dessinable (' + (err && err.message ? err.message : err) + ')';
    fig.insertBefore(sp, fig.firstChild);
  }

  function drawOne(fig) {
    var wh = SIZES[fig.getAttribute('data-size')] || SIZES.moyen, style = fig.getAttribute('data-style');
    var opts = { width: wh[0], height: wh[1], bondLength: style === 'developpee' ? 30 : 28, padding: 12, compactDrawing: false, themes: { exam: NOIR } };
    if (style === 'developpee') opts.showCarbons = 'all';           // formule développée : tous les atomes et toutes les liaisons
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', wh[0]); svg.setAttribute('height', wh[1]);
    fig.insertBefore(svg, fig.firstChild);
    try {
      var drawer = new window.SmilesDrawer.SvgDrawer(opts);
      window.SmilesDrawer.parse(fig.getAttribute('data-smiles'), function (tree) { drawer.draw(tree, svg, 'exam', false); fig.classList.add('rendered'); },
        function (err) { fail(fig, svg, err); });
    } catch (e) { fail(fig, svg, e); }
  }

  function drawMolecules(root) {
    var figs = (root || document).querySelectorAll('figure.mol[data-smiles]:not(.rendered)');
    if (figs.length) loadChem(function () { figs.forEach(drawOne); });
  }

  function renderMath(root) {
    if (window.katex) {
      (root || document).querySelectorAll('.math:not(.rendered)').forEach(function (el) {
        var tex = el.textContent;
        try {
          window.katex.render(tex, el, { displayMode: el.classList.contains('block'), throwOnError: false,
            strict: 'ignore', trust: false, output: 'htmlAndMathml', macros: Object.assign({}, window.KATEX_MACROS) });
        } catch (e) { el.textContent = tex; }
        el.classList.add('rendered');
      });
    }
    drawMolecules(root);
  }
  window.renderMath = renderMath;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { renderMath(document); });
  else renderMath(document);
})();
