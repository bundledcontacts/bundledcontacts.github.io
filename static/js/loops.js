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

  /* A video with `data-cues="<selector>"` drives a list of steps: the step whose
   * data-start the playhead has last passed is marked .is-active, and clicking a
   * step seeks to it. The list is only marked .is-synced once this runs, so with
   * JS disabled the steps render as a plain, fully legible list. */
  vids.forEach(function (v) {
    var list = v.dataset.cues && document.querySelector(v.dataset.cues);
    if (!list) return;
    var cues = [].slice.call(list.children);
    var starts = cues.map(function (c) { return parseFloat(c.dataset.start) || 0; });
    var current = -1;

    list.classList.add('is-synced');

    function mark(i) {
      if (i === current) return;
      if (cues[current]) cues[current].classList.remove('is-active');
      if (cues[i]) cues[i].classList.add('is-active');
      current = i;
    }

    v.addEventListener('timeupdate', function () {
      var t = v.currentTime, i = 0;
      while (i + 1 < starts.length && t >= starts[i + 1]) i++;
      mark(i);
    });

    cues.forEach(function (c, i) {
      c.addEventListener('click', function () {
        // play() may still have to load(), which resets currentTime -- so start
        // playback first and seek once there is a timeline to seek in.
        play(v);
        mark(i);
        if (v.readyState >= 1) v.currentTime = starts[i];
        else v.addEventListener('loadedmetadata', function () {
          v.currentTime = starts[i];
        }, { once: true });
      });
    });
  });
})();
