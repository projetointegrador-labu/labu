/* Máscaras simples (telefone, CEP) e confirmação de ações destrutivas. */
(function () {
  function mascara(tipo, v) {
    var d = v.replace(/\D/g, '');
    if (tipo === 'cep') return d.slice(0, 8).replace(/^(\d{5})(\d)/, '$1-$2');
    d = d.slice(0, 11);
    if (d.length > 10) return d.replace(/^(\d{2})(\d{5})(\d{0,4}).*/, '($1) $2-$3');
    if (d.length > 6) return d.replace(/^(\d{2})(\d{4})(\d{0,4}).*/, '($1) $2-$3');
    if (d.length > 2) return d.replace(/^(\d{2})(\d{0,5})/, '($1) $2');
    return d;
  }
  document.querySelectorAll('[data-mascara]').forEach(function (el) {
    el.addEventListener('input', function () { el.value = mascara(el.dataset.mascara, el.value); });
  });
  document.querySelectorAll('form[data-confirmar]').forEach(function (f) {
    f.addEventListener('submit', function (e) { if (!window.confirm(f.dataset.confirmar)) e.preventDefault(); });
  });
})();
