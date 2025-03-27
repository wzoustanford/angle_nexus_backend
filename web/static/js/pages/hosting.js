/*
    js of hosting
    --------------------------
    ** (Sticky elements) at scroll Down
    ScrollMagic
    --------------------------
*/

(function ($) {
  "use strict";

    jQuery(document).on('ready', function(){
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

    });

  }(jQuery));
