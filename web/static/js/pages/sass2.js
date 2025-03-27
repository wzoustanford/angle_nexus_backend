/*
    js of interior
    --------------------------
    ** (Sticky elements) at scroll Down
    --------------------------
    ** Rotate at scroll
    --------------------------
    ** Hide box--signup
    --------------------------
*/

(function ($) {
  "use strict";

  jQuery(document).on('ready', function () {

    // ScrollMagic
    $(function () {
      /*-----------------------------
      (Sticky elements) at scroll Down
    -----------------------------*/
      // build scene
      var scene = new ScrollMagic.Scene({
        triggerElement: "#target1",
        duration: 300,
      })
        .setPin("#pin1")
        .addIndicators({
          name: "1 (duration: 300)",
        }) // add indicators (requires plugin)
        .addTo(controller);

      /*-----------------------------
      Rotate at scroll
    -----------------------------*/
      // build scene
      var scene = new ScrollMagic.Scene({
        triggerElement: "#targetRotate",
      })
        .setTween("#animateRotate", 0.5, {
          left: 100,
          rotation: 20,
          ease: Circ.easeInOut,
        }) // trigger a TweenMax.to tween
        .addIndicators({
          name: "1 (duration: 0)",
        }) // add indicators (requires plugin)
        .addTo(controller);

      /*-----------------------------
      Hide box--signup
    -----------------------------*/
      // build scene
      var scene = new ScrollMagic.Scene({
        triggerElement: "#triggerForm",
      })
        // trigger animation by adding a css class
        .setClassToggle("#animate1", "translat")
        .addIndicators({
          name: "1 - add a class",
        }) // add indicators (requires plugin)
        .addTo(controller);
    });


  });

}(jQuery));
