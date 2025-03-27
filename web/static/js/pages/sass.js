/*
    js of interior
    --------------------------
    ** Hide header
    --------------------------
    ** Show header
    --------------------------
    ** horizontal scroll
    --------------------------
    ** Toggle for Pricing
    --------------------------
*/

(function ($) {
  "use strict";

  jQuery(document).on('ready', function () {

    $(function () {
      /*-----------------------------
      Hide header
    -----------------------------*/
      // build scene
      var scene = new ScrollMagic.Scene({
        triggerElement: "#triggerForm",
      })
        // trigger animation by adding a css class
        .setClassToggle("#myNavbar", "hideheader")
        .addIndicators({
          name: "1 - add a class",
        }) // add indicators (requires plugin)
        .addTo(controller);

      /*-----------------------------
      Show header
    -----------------------------*/
      // build scene
      var scene = new ScrollMagic.Scene({
        triggerElement: "#triggerTo",
      })
        // trigger animation by adding a css class
        .setClassToggle("#myNavbar", "showheader")
        .addIndicators({
          name: "1 - add a class",
        }) // add indicators (requires plugin)
        .addTo(controller);
    });

    /*-----------------------------
    horizontal scroll
  -----------------------------*/
    // init controller
    var controller = new ScrollMagic.Controller();

    var controller = new ScrollMagic.Controller();

    // define movement of panels
    var wipeAnimation = new TimelineMax().to("#slideContainer", 1, {
      x: "-55%",
    });

    // create scene to pin and link animation
    new ScrollMagic.Scene({
      triggerElement: "#pinContainer",
      triggerHook: "onLeave",
      duration: "350%",
    })
      .setPin("#pinContainer")
      .setTween(wipeAnimation)
      .addIndicators()
      .addTo(controller);

    var horizontal = new ScrollMagic.Scene({
      offset: 50,
      duration: 300,
      // reverse: false
    })

      // .addIndicators()
      .addTo(controller);

    /*-----------------------------
    Toggle for Pricing
  -----------------------------*/
    var e = document.getElementById("filt-monthly"),
      d = document.getElementById("filt-yearly"),
      t = document.getElementById("switcher"),
      m = document.getElementById("monthly"),
      y = document.getElementById("yearly");

    e.addEventListener("click", function () {
      t.checked = false;
      e.classList.add("toggler--is-active");
      d.classList.remove("toggler--is-active");
      m.classList.remove("hide");
      y.classList.add("hide");
    });

    d.addEventListener("click", function () {
      t.checked = true;
      d.classList.add("toggler--is-active");
      e.classList.remove("toggler--is-active");
      m.classList.add("hide");
      y.classList.remove("hide");
    });

    t.addEventListener("click", function () {
      d.classList.toggle("toggler--is-active");
      e.classList.toggle("toggler--is-active");
      m.classList.toggle("hide");
      y.classList.toggle("hide");
    });


  });

}(jQuery));
