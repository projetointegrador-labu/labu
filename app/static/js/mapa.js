/* Mapa de resultados com Google Maps JavaScript API (opcional, requer GOOGLE_MAPS_API_KEY).
   A lista em texto continua sendo a fonte principal de informação (acessibilidade). */
(function () {
  var el = document.getElementById('mapa');
  if (!el || !window.LABU || !window.LABU.mapsKey) return;

  window.initLabuMap = function () {
    fetch('/api/prestadores' + window.location.search, { headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (itens) {
        if (!itens.length) return;
        el.hidden = false;
        var mapa = new google.maps.Map(el, { zoom: 11, center: { lat: itens[0].lat, lng: itens[0].lng }, mapTypeControl: false });
        var limites = new google.maps.LatLngBounds();
        var janela = new google.maps.InfoWindow();
        itens.forEach(function (i) {
          var pos = { lat: i.lat, lng: i.lng };
          var m = new google.maps.Marker({ position: pos, map: mapa, title: i.nome + ' — ' + i.categoria });
          m.addListener('click', function () {
            var div = document.createElement('div');
            var strong = document.createElement('strong'); strong.textContent = i.nome;
            var p = document.createElement('p'); p.textContent = i.categoria + ' · ' + (i.bairro || i.cidade);
            var a = document.createElement('a'); a.href = i.url; a.textContent = 'Ver perfil';
            div.append(strong, p, a);
            janela.setContent(div); janela.open(mapa, m);
          });
          limites.extend(pos);
        });
        if (itens.length > 1) mapa.fitBounds(limites);
      })
      .catch(function () { /* sem mapa: a lista continua disponível */ });
  };

  var s = document.createElement('script');
  s.src = 'https://maps.googleapis.com/maps/api/js?key=' + encodeURIComponent(window.LABU.mapsKey) + '&callback=initLabuMap';
  s.async = true; s.defer = true;
  document.head.appendChild(s);
})();
