/* Perfil do prestador: preenchimento por CEP (ViaCEP), GPS e geocodificação (Google Maps). */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var status = $('status-localizacao');
  var say = function (t) { if (status) status.textContent = t; };

  // --- CEP -> endereço (ViaCEP) ---
  var cep = $('cep');
  if (cep) cep.addEventListener('blur', function () {
    var d = cep.value.replace(/\D/g, '');
    if (d.length !== 8) return;
    say('Consultando CEP…');
    fetch('https://viacep.com.br/ws/' + d + '/json/')
      .then(function (r) { return r.json(); })
      .then(function (e) {
        if (e.erro) { say('CEP não encontrado. Preencha manualmente.'); return; }
        if (e.bairro) $('bairro').value = e.bairro;
        if (e.localidade) $('cidade').value = e.localidade;
        if (e.uf) $('estado').value = e.uf;
        say('Endereço preenchido a partir do CEP.');
      })
      .catch(function () { say('Não foi possível consultar o CEP. Preencha manualmente.'); });
  });

  // --- GPS ---
  var gps = $('btn-gps');
  if (gps && 'geolocation' in navigator) {
    gps.hidden = false;
    gps.addEventListener('click', function () {
      say('Obtendo localização…');
      navigator.geolocation.getCurrentPosition(function (p) {
        $('latitude').value = p.coords.latitude.toFixed(6);
        $('longitude').value = p.coords.longitude.toFixed(6);
        say('Localização preenchida.');
      }, function () { say('Não foi possível obter a localização. Digite as coordenadas ou use o endereço.'); },
      { timeout: 10000 });
    });
  }

  // --- Geocodificação pelo endereço (Google Maps) ---
  var geo = $('btn-geocodificar');
  if (geo && window.LABU && window.LABU.mapsKey) {
    var carregado = false, geocoder = null;
    window.initLabuGeo = function () { carregado = true; geocoder = new google.maps.Geocoder(); };
    var s = document.createElement('script');
    s.src = 'https://maps.googleapis.com/maps/api/js?key=' + encodeURIComponent(window.LABU.mapsKey) + '&callback=initLabuGeo';
    s.async = true; document.head.appendChild(s);

    geo.addEventListener('click', function () {
      if (!carregado) { say('O serviço de mapas ainda está carregando. Tente novamente.'); return; }
      var end = [$('cep').value, $('bairro').value, $('cidade').value, $('estado').value, 'Brasil'].filter(Boolean).join(', ');
      say('Localizando endereço…');
      geocoder.geocode({ address: end, region: 'BR' }, function (res, st) {
        if (st === 'OK' && res[0]) {
          var l = res[0].geometry.location;
          $('latitude').value = l.lat().toFixed(6);
          $('longitude').value = l.lng().toFixed(6);
          say('Localização encontrada: ' + res[0].formatted_address);
        } else { say('Endereço não encontrado. Confira os dados ou use o GPS.'); }
      });
    });
  }
})();
