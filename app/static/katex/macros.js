/* Raccourcis disponibles dans toutes les formules ($...$).
   Ensembles : \R, \N, \Z, \Q, \C.
   Schémas de Lewis (doublets non liants) : \lT{O} doublet au-dessus, \lB{O} en dessous, \lTB{O} dessus et dessous,
   \lLR{O} à gauche et à droite, \lTBR{Cl} dessus, dessous, droite, \lAll{Cl} les quatre côtés (ex. ion chlorure), \lone{N} électron célibataire. */
(typeof window !== 'undefined' ? window : globalThis).KATEX_MACROS = {
  '\\R': '\\mathbb{R}', '\\N': '\\mathbb{N}', '\\Z': '\\mathbb{Z}', '\\Q': '\\mathbb{Q}', '\\C': '\\mathbb{C}',
  '\\lT': '\\overset{\\cdot\\cdot}{\\mathrm{#1}}',
  '\\lB': '\\underset{\\cdot\\cdot}{\\mathrm{#1}}',
  '\\lTB': '\\underset{\\cdot\\cdot}{\\overset{\\cdot\\cdot}{\\mathrm{#1}}}',
  '\\lLR': '{:}\\mathrm{#1}{:}',
  '\\lTBR': '\\underset{\\cdot\\cdot}{\\overset{\\cdot\\cdot}{\\mathrm{#1}}}{:}',
  '\\lAll': '{:}\\underset{\\cdot\\cdot}{\\overset{\\cdot\\cdot}{\\mathrm{#1}}}{:}',
  '\\lone': '\\overset{\\cdot}{\\mathrm{#1}}'
};
