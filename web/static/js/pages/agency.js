/*
    js of Crypto dark
    --------------------------
    ** ScrollMagic (animation on text)
    --------------------------
    ** Particles
    --------------------------
*/

(function ($) {
  "use strict";

    jQuery(document).on('ready', function(){

      /*-----------------------------
      ScrollMagic (animation on text)
    -----------------------------*/
      var scene = new ScrollMagic.Scene({
          triggerElement: "#triggerBlur",
        })
        // trigger animation by adding a css class
        .setClassToggle("#Statistic", "animetext")
        .addIndicators({
          name: "1 - add a class",
        }) // add indicators (requires plugin)
        .addTo(controller);

        /*-----------------------------
        Particles
      -----------------------------*/
        particlesJS("particles-js", {
          particles: {
            number: {
              value: 8,
              density: {
                enable: true,
                value_area: 800,
              },
            },
            color: {
              value: ["#165DF5", "#19A389", "#F28E1C", "#F93542"],
            },
            shape: {
              type: ["circle"],
              stroke: {
                width: 0,
                color: "#000000",
              },
              polygon: {
                nb_sides: 5,
              },
            },
            opacity: {
              value: 1,
              random: true,
              anim: {
                enable: false,
                speed: 1,
                opacity_min: 0.6,
                sync: false,
              },
            },
            size: {
              value: 8,
              random: true,
              anim: {
                enable: false,
                speed: 40,
                size_min: 0.3,
                sync: false,
              },
            },
            line_linked: {
              enable: false,
              distance: 500,
              color: "#ffffff",
              opacity: 1,
              width: 2,
            },
            move: {
              enable: true,
              speed: 0.5,
              direction: "none",
              random: false,
              straight: false,
              out_mode: "out",
              bounce: false,
              attract: {
                enable: false,
                rotateX: 600,
                rotateY: 1200,
              },
            },
          },
        });

    });

  }(jQuery));
