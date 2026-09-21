/* Looping result clips.
 *
 * The page carries a dozen short loops. Letting them all autoplay on load means
 * a dozen simultaneous downloads, so each one is marked `data-loop` with
 * preload="none" and is only fetched and played once it is actually on screen;
 * off-screen clips are paused again.
 *
 * The `autoplay` attribute stays on the elements, so with JS disabled the
 * browser still plays them -- this only makes the loading polite, it is not
 * what makes them work.
 */
(function () {
  var vids = [].slice.call(document.querySelectorAll('video[data-loop]'));
  if (!vids.length) return;

  function play(v) {
    if (v.preload !== 'auto') {
      v.preload = 'auto';
      v.load();
    }
    var p = v.play();
    if (p && p.catch) p.catch(function () { /* autoplay blocked; ignore */ });
  }

  if (!('IntersectionObserver' in window)) {
    vids.forEach(play);
    return;
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) play(e.target);
      else if (!e.target.paused) e.target.pause();
    });
  }, { rootMargin: '200px 0px', threshold: 0.1 });

  vids.forEach(function (v) { io.observe(v); });
})();
