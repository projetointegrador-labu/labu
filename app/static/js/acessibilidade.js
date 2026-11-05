/* Preferências de acessibilidade: tamanho da fonte, alto contraste e redução de movimento.
   Persistidas em localStorage. Executa cedo (no <head>) para evitar "piscar" de estilo. */
(function () {
  var CHAVE = 'labu:a11y';
  var raiz = document.documentElement;
  var prefs = { fonte: 0, contraste: false, movimento: false, claro: false };

  function ler() {
    try {
      var salvo = JSON.parse(localStorage.getItem(CHAVE) || '{}');
      prefs.fonte = Math.max(-1, Math.min(3, parseInt(salvo.fonte, 10) || 0));
      prefs.contraste = salvo.contraste === true ||
        (salvo.contraste === undefined && window.matchMedia && matchMedia('(prefers-contrast: more)').matches);
      prefs.movimento = salvo.movimento === true;
      prefs.claro = salvo.claro === true;
    } catch (e) { /* storage indisponível: usa padrões */ }
  }
  function salvar() { try { localStorage.setItem(CHAVE, JSON.stringify(prefs)); } catch (e) {} }
  function aplicar() {
    if (prefs.fonte) raiz.setAttribute('data-fonte', String(prefs.fonte)); else raiz.removeAttribute('data-fonte');
    raiz.classList.toggle('alto-contraste', prefs.contraste);
    raiz.classList.toggle('sem-movimento', prefs.movimento);
    raiz.classList.toggle('tema-claro', prefs.claro);
  }
  function anunciar(msg) {
    var r = document.getElementById('mensagens');
    if (r) { var p = document.createElement('p'); p.className = 'sr-only'; p.textContent = msg; r.appendChild(p); setTimeout(function () { p.remove(); }, 3000); }
  }

  ler(); aplicar();

  document.addEventListener('DOMContentLoaded', function () {
    var botoes = document.querySelectorAll('[data-a11y]');
    function sincronizar() {
      botoes.forEach(function (b) {
        if (b.dataset.a11y === 'contraste') b.setAttribute('aria-pressed', String(prefs.contraste));
        if (b.dataset.a11y === 'movimento') b.setAttribute('aria-pressed', String(prefs.movimento));
        if (b.dataset.a11y === 'tema') b.setAttribute('aria-pressed', String(prefs.claro));
      });
    }
    sincronizar();
    botoes.forEach(function (b) {
      b.addEventListener('click', function () {
        var a = b.dataset.a11y, msg = '';
        if (a === 'fonte-mais') { prefs.fonte = Math.min(3, prefs.fonte + 1); msg = 'Texto maior'; }
        if (a === 'fonte-menos') { prefs.fonte = Math.max(-1, prefs.fonte - 1); msg = 'Texto menor'; }
        if (a === 'fonte-padrao') { prefs.fonte = 0; msg = 'Tamanho de texto padrão'; }
        if (a === 'contraste') { prefs.contraste = !prefs.contraste; msg = prefs.contraste ? 'Alto contraste ativado' : 'Alto contraste desativado'; }
        if (a === 'tema') { prefs.claro = !prefs.claro; msg = prefs.claro ? 'Tema claro ativado' : 'Tema escuro ativado'; }
        if (a === 'movimento') { prefs.movimento = !prefs.movimento; msg = prefs.movimento ? 'Animações reduzidas' : 'Animações normais'; }
        aplicar(); salvar(); sincronizar(); anunciar(msg);
      });
    });

    // Move o foco ao conteúdo ao ativar o link "pular"
    var skip = document.querySelector('.skip-link'), main = document.getElementById('conteudo');
    if (skip && main) skip.addEventListener('click', function () { setTimeout(function () { main.focus(); }, 0); });

    // Se houver resumo de erros, leva o foco até ele
    var resumo = document.getElementById('resumo-erros');
    if (resumo) resumo.focus();
  });
})();
