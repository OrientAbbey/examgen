/* Rendu des formules : le serveur produit <span class="math inline">LaTeX</span> (ou <div class="math block">) ;
   KaTeX (+ mhchem pour la chimie : \ce{H2O}, \pu{m.s-1}) les met en forme dans le navigateur, écran comme impression. */
(function () {
  function renderMath(root) {
    if (!window.katex) return;
    (root || document).querySelectorAll('.math:not(.rendered)').forEach(function (el) {
      var tex = el.textContent;
      try {
        window.katex.render(tex, el, { displayMode: el.classList.contains('block'), throwOnError: false,
          strict: 'ignore', trust: false, output: 'htmlAndMathml', macros: Object.assign({}, window.KATEX_MACROS) });
      } catch (e) { el.textContent = tex; }
      el.classList.add('rendered');
    });
  }
  window.renderMath = renderMath;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { renderMath(document); });
  else renderMath(document);
})();
