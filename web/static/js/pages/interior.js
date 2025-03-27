/*
    js of interior
    --------------------------
    ** Hide header
    --------------------------
    ** Show header
    --------------------------
    ** horizontal scroll
    --------------------------
    ** SimpleParallax
    --------------------------
*/

(function ($) {
  "use strict";

    jQuery(document).on('ready', function(){

      $(function() {
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
      SimpleParallax
      -----------------------------*/
      var image = document.getElementsByClassName("thumbnail");
      new simpleParallax(image, {
        delay: 0.6,
        transition: "cubic-bezier(0,0,0,1)",
      });


    });

  }(jQuery));
