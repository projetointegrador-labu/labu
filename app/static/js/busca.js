/* Busca por proximidade usando a Geolocation API do navegador. */
(function () {
  var btn = document.getElementById('btn-localizacao');
  var status = document.getElementById('status-localizacao');
  var lat = document.getElementById('lat');
  var lng = document.getElementById('lng');
  if (!btn || !lat || !lng) return;

  if (!('geolocation' in navigator)) { return; }   // botão permanece oculto
  btn.hidden = false;

  var form = btn.closest('form');
  // Se o usuário editar bairro/cidade, a busca por GPS é descartada
  ['bairro', 'cidade'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('input', function () { lat.value = ''; lng.value = ''; });
  });

  btn.addEventListener('click', function () {
    status.textContent = 'Obtendo sua localização…';
    btn.disabled = true;
    navigator.geolocation.getCurrentPosition(function (pos) {
      lat.value = pos.coords.latitude.toFixed(6);
      lng.value = pos.coords.longitude.toFixed(6);
      status.textContent = 'Localização obtida. Buscando profissionais próximos…';
      form.submit();
    }, function (err) {
      btn.disabled = false;
      var msgs = { 1: 'Permissão de localização negada. Informe bairro ou cidade manualmente.',
                   2: 'Não foi possível determinar sua localização.',
                   3: 'Tempo esgotado ao obter a localização.' };
      status.textContent = msgs[err.code] || 'Falha ao obter localização.';
    }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 });
  });
})();
