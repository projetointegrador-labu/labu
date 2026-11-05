/* Busca: localização (Geolocation API), rótulo do slider de diária e ordenação. */
(function () {
  // --- "Usar minha localização" ---
  var btn = document.getElementById('btn-localizacao');
  var status = document.getElementById('status-localizacao');
  var lat = document.getElementById('lat');
  var lng = document.getElementById('lng');
  if (btn && lat && lng && 'geolocation' in navigator) {
    btn.hidden = false;
    var form = btn.closest('form');
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
        var msgs = { 1: 'Permissão de localização negada. Informe cidade ou bairro no campo de busca.',
                     2: 'Não foi possível determinar sua localização.',
                     3: 'Tempo esgotado ao obter a localização.' };
        status.textContent = msgs[err.code] || 'Falha ao obter localização.';
      }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 });
    });
  }

  // --- Slider de diária: atualiza o texto ao lado do rótulo ---
  var slider = document.getElementById('diaria_max');
  var saida = document.getElementById('diaria-saida');
  if (slider && saida) {
    var atualizar = function () {
      saida.textContent = Number(slider.value) >= Number(slider.max) ? 'qualquer valor' : 'R$ ' + slider.value;
    };
    slider.addEventListener('input', atualizar);
    atualizar();
  }

  // --- Ordenação: a lista é atualizada ao escolher (o usuário é avisado via aria-describedby) ---
  var ordem = document.getElementById('ordem');
  if (ordem && ordem.form) {
    ordem.addEventListener('change', function () { ordem.form.submit(); });
  }
})();
