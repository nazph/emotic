/* global requirejs AddressPicker google EmoEngine EdkDll ELSPlugin platform StartEdk
 disconnectHeadset connectedHeadset onloadPluginEmotiv loaduserProfile
 isThreeSensorsStatus:true */
define(['loglevel',
    'platform'
], function(log,platform) {
  const VERSION = "1.9.1.3";
  window.ELSPlugin = function() {
    return document.getElementById('plugin0');
  }
  function pluginLoaded() {
    log.debug("Plugin loaded!");
  }
  function checkPluginExists() {
    var L = navigator.plugins.length;
    for (var i = 0; i < L; i++) {
      log.debug(
          navigator.plugins[i].name +
          " | " +
          navigator.plugins[i].filename +
          " | " +
          navigator.plugins[i].description +
          " | " +
          navigator.plugins[i].version +
          "<br>"
          );
      if (navigator.plugins[i].name === "EmotivBTLE") {
        return true;
      }
    }
    return false;
  }
  function downloadPlugin() {
    var confirmUpdate = false;
    if ((platform.os.family === "OS X") || (platform.os.family === "iOS")) {
      confirmUpdate = confirm("Please update new version " +
          "of Emotiv plugin. You may need to restart your browser " +
          "to complete installation.");
      if (confirmUpdate === true) {
        window.location.href = ('/static/EmotivBTLE.dmg');
      }
    } else {
      confirmUpdate = confirm("Please update new version of Emotiv plugin. " +
          "You may need to restart your browser to complete installation.");
      if (confirmUpdate === true) {
        window.location.href = ('/static/EmotivBTLE.msi');
      }
    }
  }
  function onloadPluginEmotiv() {
    var isInternetExplorer = !navigator.userAgent.match(/Trident.*rv\\:11\./);
    if (!checkPluginExists() && !isInternetExplorer) {
      var is_chrome = navigator.userAgent.toLowerCase().indexOf('chrome') > -1;
      if (is_chrome) {
        var chromeVersion = navigator.userAgent.match(/Chrom(e|ium)\/([0-9]+)\./);
        chromeVersion = chromeVersion ? parseInt(chromeVersion[2], 10) : false;
        if (chromeVersion >= 45) {
          alert("Your browser is Google's Chrome version 45 or higher " +
              "which is not support our plugin. Please run the Cpanel " +
              "website with Google's Chrome version lower 45 or another " +
              "Web Browsers. Thanks.");
        } else {
          downloadPlugin();
        }
      } else {
        downloadPlugin();
      }
    } else {
      var version = ELSPlugin().version;
      if (version === undefined && isInternetExplorer) {
        downloadPlugin();
      }
      if (version !== null) {
        if ((platform.os.family === "OS X") || (platform.os.family === "iOS")) {
          if (version !== VERSION) {
            downloadPlugin();
          }
        } else if (version !== VERSION) {
          downloadPlugin();
        }
      }
    }
  }
  var isBlack;
  var isRed;
  var isYellow;
  var isGreen;
  /* -- Draw Headset --*/
  var image0 = ["/static/images/headset/f3-black.png",
      "/static/images/headset/f3-red.png",
      "/static/images/headset/f3-yellow.png",
      "/static/images/headset/f3-green.png"];
  var image1 = ["/static/images/headset/f4-black.png",
      "/static/images/headset/f4-red.png",
      "/static/images/headset/f4-yellow.png",
      "/static/images/headset/f4-green.png"];
  var image2 = ["/static/images/headset/t7-black.png",
      "/static/images/headset/t7-red.png",
      "/static/images/headset/t7-yellow.png",
      "/static/images/headset/t7-green.png"];
  var image3 = ["/static/images/headset/t8-black.png",
      "/static/images/headset/t8-red.png",
      "/static/images/headset/t8-yellow.png",
      "/static/images/headset/t8-green.png"];
  var image4 = ["/static/images/headset/pz-black.png",
      "/static/images/headset/pz-red.png",
      "/static/images/headset/pz-yellow.png",
      "/static/images/headset/pz-green.png"];

  var smallNote = [];
  smallNote = document.getElementsByName("smallNote");
  /* HERE */
  var smallNoteBaseline1 = [];
  smallNoteBaseline1 = document.getElementsByName("smallNoteBaseline1");
  var smallNoteBaseline2 = [];
  smallNoteBaseline2 = document.getElementsByName("smallNoteBaseline2");
  var smallNoteBaseline11 = [];
  smallNoteBaseline11 = document.getElementsByName("smallNoteBaseline11");
  var smallNoteBaseline22 = [];
  smallNoteBaseline22 = document.getElementsByName("smallNoteBaseline22");
  var noteValue = []; // store value of each note

  $(document).bind("EmoEngineEmoStateUpdated", function(event, userId, es) {
    isThreeSensorsStatus = true;
    var numNoteValue = 0;
    var signalStatus = es.IS_GetWirelessSignalStatus();
    if (signalStatus === 0) {
      var i = 0;
      for (i = 0; i < 5; i++) {
        noteValue[i] = 0;
      }
    } else {
      var contactQualityChannels = [];
      contactQualityChannels = es.IS_GetContactQualities();
      noteValue[0] = contactQualityChannels[0];
      if (noteValue[0] === 4) numNoteValue++;
      noteValue[1] = contactQualityChannels[1];
      if (noteValue[1] === 4) numNoteValue++;
      noteValue[2] = contactQualityChannels[2];
      if (noteValue[2] === 4) numNoteValue++;
      noteValue[3] = contactQualityChannels[3];
      if (noteValue[3] === 4) numNoteValue++;
      noteValue[4] = contactQualityChannels[4];
      if (noteValue[4] === 4) numNoteValue++;
      if (numNoteValue > 2) {
        isThreeSensorsStatus = true;
      } else {
        isThreeSensorsStatus = false;
      }
      isThreeSensorsStatus = true;
    }
    /* -- Update headset small --*/
    isBlack = 0;
    isRed = 0;
    isYellow = 0;
    isGreen = 0;
    /* -- End update --*/
    drawNote();
  });

  function noteStatus(noteValue, i) {
    // O: Black
    // 1: Red
    // 2: Orange
    // 3: Orange
    // 4: Green
    var returnImg = new Image();
    if (i === 0) {
      switch (noteValue) {
        case 0:
          returnImg.src = image0[0];
          isBlack++;
          break;
        case 1:
          returnImg.src = image0[1];
          isRed++;
          break;
        case 2:
          returnImg.src = image0[2];
          isYellow++;
          break;
        case 3:
          returnImg.src = image0[2];
          isYellow++;
          break;
        case 4:
          returnImg.src = image0[3];
          isGreen++;
          break;
        default :
          returnImg.src = image0[0];
      }
    } else if (i === 1) {
      switch (noteValue) {
        case 0:
          returnImg.src = image1[0];
          isBlack++;
          break;
        case 1:
          returnImg.src = image1[1];
          isRed++;
          break;
        case 2:
          returnImg.src = image1[2];
          isYellow++;
          break;
        case 3:
          returnImg.src = image1[2];
          isYellow++;
          break;
        case 4:
          returnImg.src = image1[3];
          isGreen++;
          break;
        default :
          returnImg.src = image1[0];
      }
    } else if (i === 2) {
      switch (noteValue) {
        case 0:
          returnImg.src = image2[0];
          isBlack++;
          break;
        case 1:
          returnImg.src = image2[1];
          isRed++;
          break;
        case 2:
          returnImg.src = image2[2];
          isYellow++;
          break;
        case 3:
          returnImg.src = image2[2];
          isYellow++;
          break;
        case 4:
          returnImg.src = image2[3];
          isGreen++;
          break;
        default :
          returnImg.src = image2[0];
      }
    } else if (i === 3) {
      switch (noteValue) {
        case 0:
          returnImg.src = image3[0];
          isBlack++;
          break;
        case 1:
          returnImg.src = image3[1];
          isRed++;
          break;
        case 2:
          returnImg.src = image3[2];
          isYellow++;
          break;
        case 3:
          returnImg.src = image3[2];
          isYellow++;
          break;
        case 4:
          returnImg.src = image3[3];
          isGreen++;
          break;
        default :
          returnImg.src = image3[0];
      }
    } else if (i === 4) {
      switch (noteValue) {
        case 0:
          returnImg.src = image4[0];
          isBlack++;
          break;
        case 1:
          returnImg.src = image4[1];
          isRed++;
          break;
        case 2:
          returnImg.src = image4[2];
          isYellow++;
          break;
        case 3:
          returnImg.src = image4[2];
          isYellow++;
          break;
        case 4:
          returnImg.src = image4[3];
          isGreen++;
          break;
        default :
          returnImg.src = image4[0];
      }
    }
    return returnImg;
  }

  function drawNote() {
    smallNote[0].src = noteStatus(noteValue[0], 0).src;
    // AF3 = 0, T7 = 1, Pz = 2, T8 = 3, AF4 = 4;
    smallNote[1].src = noteStatus(noteValue[4], 1).src;
    smallNote[2].src = noteStatus(noteValue[1], 2).src;
    smallNote[3].src = noteStatus(noteValue[3], 3).src;
    smallNote[4].src = noteStatus(noteValue[2], 4).src;
    if (isYellow > 0 || isGreen > 0) {
      smallNote[5].src = "/static/images/headset/cfr-green.png";
    } else {
      smallNote[5].src = "/static/images/headset/cfr-red.png";
    }
  }

  function disconnectHeadset() {
    // alert("Headset connection lost. Please check that your headset is turned on, and bluetooth is enabled on your computer");
    // isAlertLostConnection = true;
    $('#baseline').removeClass('hidden');
  }

  function connectedHeadset() {
    $('#baseline').removeClass('hidden');
  }
  // check connected
  var isConnected = false;

  return {
    onloadPluginEmotiv: onloadPluginEmotiv,
    isConnected: isConnected,
  }
});
