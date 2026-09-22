/* Hover readout for the contact-scaling plot in the Method overview.
 *
 * The curves themselves are static SVG, so the figure reads fine without JS;
 * this only adds a crosshair and a tooltip with s_kappa(d) for each stiffness
 * at the hovered penetration depth.
 */
(function () {
  var fig = document.getElementById('contact-plot');
  if (!fig) return;

  var svg = fig.querySelector('svg');
  var hit = fig.querySelector('.cp-hit');
  var cross = fig.querySelector('.cp-cross');
  var dots = fig.querySelectorAll('.cp-dot');
  var tip = fig.querySelector('.contact-plot-tip');
  var ds = fig.dataset;
  var x0 = +ds.x0, x1 = +ds.x1, L = +ds.left, R = +ds.right, T = +ds.top, B = +ds.bottom;
  var W = +ds.width, H = +ds.height;
  var kappas = [50, 100, 300];

  function s(k, dCm) { return 1 / (1 + Math.exp(-k * dCm / 100)); }
  function xOf(d) { return L + (d - x0) / (x1 - x0) * (W - L - R); }
  function yOf(v) { return T + (1 - v) * (H - T - B); }

  function show(clientX) {
    var box = svg.getBoundingClientRect();
    var scale = box.width / W;
    var px = (clientX - box.left) / scale;
    var d = x0 + (px - L) / (W - L - R) * (x1 - x0);
    d = Math.max(x0, Math.min(x1, d));
    var x = xOf(d);

    cross.setAttribute('x1', x);
    cross.setAttribute('x2', x);
    var rows = ['<div>d = ' + d.toFixed(1) + ' cm</div>'];
    kappas.forEach(function (k, i) {
      var v = s(k, d);
      dots[i].setAttribute('cx', x);
      dots[i].setAttribute('cy', yOf(v));
      rows.push('<div class="cp-row"><i class="cp-swatch cp-k' + k + '"></i>&kappa; = ' + k +
                '<b>' + v.toFixed(2) + '</b></div>');
    });
    tip.innerHTML = rows.join('');
    fig.classList.add('is-hovering');

    // keep the tooltip beside the crosshair, flipping sides near the right edge
    var tw = tip.offsetWidth;
    var left = x * scale + 12;
    if (left + tw > box.width) left = x * scale - tw - 12;
    tip.style.left = Math.max(0, Math.min(left, box.width - tw)) + 'px';
    tip.style.top = (T * scale + 6) + 'px';
  }

  function hide() { fig.classList.remove('is-hovering'); }

  hit.addEventListener('pointermove', function (e) { show(e.clientX); });
  hit.addEventListener('pointerdown', function (e) { show(e.clientX); });
  hit.addEventListener('pointerleave', hide);
})();
