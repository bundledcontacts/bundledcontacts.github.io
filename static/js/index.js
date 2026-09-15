window.HELP_IMPROVE_VIDEOJS = false;

$(document).ready(function () {
  // Toggle the mobile navigation menu, if a navbar is present.
  $(".navbar-burger").click(function () {
    $(".navbar-burger").toggleClass("is-active");
    $(".navbar-menu").toggleClass("is-active");
  });

  // Initialize any carousel on the page (none by default).
  var options = {
    slidesToScroll: 1,
    slidesToShow: 3,
    loop: true,
    infinite: true,
    autoplay: false,
    autoplaySpeed: 3000,
  };
  bulmaCarousel.attach('.carousel', options);

  bulmaSlider.attach();
});
