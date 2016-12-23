/* global requirejs AddressPicker google EmoEngine EdkDll ELSPlugin platform StartEdk
 disconnectHeadset connectedHeadset onloadPluginEmotiv loaduserProfile  */

// Use requireJS to pull all things together in browser
requirejs([
  'jquery',
  'loglevel',
  'es6-polyfill',
  'googleMaps',
  'typeahead-addresspicker.min',
  'hoverIntent',
  'superfish',
  'jquery-ui',
  'platform',
  'headset',
  'baseline'
], function(
  $,
  log,
  a,
  b,
  c,
  d,
  e,
  f,
  platform,
  headset,
  baseline
) {
  $(document).ready(function() {
    // For Set Attributes page
    if ($("#set_attributes").length > 0) {
      // Datepicker for date picking
      $(".datepicker").datepicker({
        dateFormat: "yy-mm-dd"
      });
      // For birthday it needs to be in past only
      if ($("input[name='date of birth']").length > 0) {
        $("input[name='date of birth']").datepicker("destroy");
        $("input[name='date of birth']").datepicker({
          dateFormat: "yy-mm-dd",
          maxDate: new Date()
        });
        // Check for errors in date of birth
        $("input[name='date of birth']").change(function(e) {
          checkForBirthdayError();
        });
      }

      // For typeahead for google
      var addressPicker = new AddressPicker();
      var addresses = new Set();
      $('#address').typeahead({highlight: true, hint: false}, {
        displayKey: 'description',
        source: addressPicker.ttAdapter()
      }).on('keydown', function(e) {
        // Tab highlights first selection.
        if (e.which === 9) {
          var newE = $.Event('keydown');
          newE.keyCode = newE.which = 40; // arrow down
          $('#address').trigger(newE);
          e.preventDefault();
        }
      }).on('keyup', function(e) {
        $('.tt-suggestion').each(function(_, suggestion) {
          addresses.add($(suggestion).text());
        });
      });

      // Validate on submit.
      $("#set_attributes").submit(function(e) {
        e.preventDefault();
        if (!checkForBirthdayError() && !checkForAddressError(addresses)) {
          $("#set_attributes")[0].submit();
        }
      });
    }
  });

  function checkForAddressError(addresses) {
    // Address errors.
    var address = $("#address").val();
    if (address && addresses.size && !addresses.has(address)) {
      appendError(
          "#address",
          "location_error",
          "Please select an address from the list.");
      return true;
    }
    clearError("location_error");
    return false;
  }

  function appendError(after, id, error) {
    if ($('#' + id).length > 0) {
      $('#' + id).html(error);
    } else {
      $(after).parent().after('<p id="' + id + '">' + error + '</p>');
    }
  }

  function clearError(id) {
    $('#' + id).remove();
  }

  // Birthday error
  function checkForBirthdayError() {
    var dob = $("input[name='date of birth']");
    // If blank
    if (!dob.val()) {
      return false;
    }

    var today = new Date();
    var bday = new Date(dob.val());
    bday = new Date(bday.getTime() + bday.getTimezoneOffset() * 60000);

    // Future birth check
    if (bday > today) {
      dob.val("");
      appendError(
          dob, "date_of_birth_error", "You cannot be born in the future.");
      return true;
    }
    clearError("date_of_birth_error");
    return false;
  }
  /**
   *  * Main script for connect to engine, update data ...
   *  * Set Global Vars here
   *   */
  /**
   * update emoengine to get data
   */
  function updateEmoEngine() {
    try {
      var timeStopConnection = new Date();
      if (((timeStopConnection.getTime() - timeConnection.getTime()) > 2000) &&
          headset.isConnected) {
        isLostConnection = true;
      } else if (((timeStopConnection.getTime() -
              timeConnection.getTime()) < 2000) && headset.isConnected) {
        isLostConnection = false;
      }
      if (isLostConnection && (!isAlertLostConnection)) {
        alert("Headset connection lost. " +
            "Please check that your headset is turned on, " +
            "and bluetooth is enabled on your computer");
        isAlertLostConnection = true;
        disconnectHeadset();
        openPopup(".baseline_start");
      }
      if (!isLostConnection && isAlertLostConnection) {
        isAlertLostConnection = false;
        connectedHeadset();
      }
      if ((platform.os.family === "OS X") || (platform.os.family === "iOS")) {
        var numberDevice = ELSPlugin().ELS_IEE_GetInsightDeviceCount();
        if (numberDevice > 0 && !headset.isConnected) {
          log.debug(ELSPlugin().ELS_IEE_ConnectInsightDevice(0));
        }
      }
      engine.IProcessEvents(1000);
      if (isStopUpdateEmoEngine === false) {
        setTimeout(updateEmoEngine, 500);
      }
    } catch (e) {
      alert(e);
      if (!isLostConnection) timeConnection = new Date();
    }
  }

  /**
   * Proccess Login
   */
  function proccessLogin() {
    if ((platform.os.family === "OS X") || (platform.os.family === "iOS")) {
      log.debug("OS X");
      ELSPlugin().ELS_IEE_EmoInitDevice();
    }
    engine.IConnect();
    var x1 = EdkDll.IEE_GetSecurityCode();
    EdkDll.IEE_CheckSecurityCode(x1);
    updateEmoEngine();
  }
  /**
   * Add event check valid to website
   */
  function addValidLicenseDoneEvent() {
    EdkDll.addEvent(ELSPlugin(), 'valid', function(license) {
      if (license.indexOf('"License":"EEG"') > -1) {
        log.debug("License is EEG License. You can get all data.");
      } else if (license.indexOf('"License":"Non-EEG"') > -1) {
        log.debug("License is Non-EEG License. " +
            "You can get all non-eeg data.");
      } else {
        log.debug("The license is not valid. " +
            "Please get valid license to get data");
      }
      proccessLogin();
    });
  }

  /**
   * init connect and update data
   */
  function init() {
    headset.onloadPluginEmotiv();
    addValidLicenseDoneEvent();
    EdkDll.ELS_ValidLicense();
    // EdkDll.DebugLog = true;
    isFacial = false;
    isPerformance = false;
    sysTime = document.getElementById("txtInputTime");
    sysTime.value = "00.00";
  }

  // EMOTIV HEADSET INFO
  if ($("#headset").length > 0) {
    $(document).bind("UserAdded", function(event, userId) {
      headset.isConnected = true;
      timeConnection = new Date();
      var headsetVersion = EdkDll.IEE_HardwareGetVersion(userId);

      if (((headsetVersion >> 16) !==
            EdkDll.IEE_HeadsetVersion_t.IEE_INSIGHT_EEG_OLD) &&
          ((headsetVersion >> 16) !==
           EdkDll.IEE_HeadsetVersion_t.IEE_INSIGHT_NOEEG1_OLD) &&
          ((headsetVersion >> 16) !==
           EdkDll.IEE_HeadsetVersion_t.IEE_INSIGHT_NOEEG2_OLD)) {
        log.debug("Insight EEG Old");
      }

      if (((headsetVersion >> 24) !==
            EdkDll.IEE_HeadsetVersion_t.IEE_INSIGHT_EEG1_NEW) &&
          ((headsetVersion >> 24) !==
           EdkDll.IEE_HeadsetVersion_t.IEE_INSIGHT_EEG2_NEW) &&
          ((headsetVersion >> 24) !==
           EdkDll.IEE_HeadsetVersion_t.IEE_INSIGHT_NOEEG1_NEW) &&
          ((headsetVersion >> 24) !==
           EdkDll.IEE_HeadsetVersion_t.IEE_INSIGHT_NOEEG2_NEW)) {
        log.debug("Insight EEG New");
      }
      if (isEmotivIDLogin === true) {
        var profileName = document.getElementById('select-profile').value;
        loaduserProfile(profileName);
      }
      if (isGuestLogin === true) {
        EdkDll.EE_SetBaseProfile(0);
        log.debug("Load profile");
      }
      baseline.StartEdk();
    });

    $('#confirmAdjustment').click(function() {
        // Check if at least three sensors are green here
      $('#adjustment-text').hide();
      $('.headset-adjustment-container').hide();
      $('#baseline-button').show();
      startCamera();
    });

    $(document).bind("EmoStateUpdated", function(event, userId, es) {
      var getTime = es.IS_GetTimeFromStart();
      getTime = Math.round(getTime * 100) / 100;
      sysTime.value = getTime;
      // var batteryArr = es.IS_GetBatteryChargeLevel();
      // var batteryPercent = (batteryArr.chargeLevel / batteryArr.maxLevel) * 100;

      timeConnection = new Date();
    });

    // Disable init because we aren't using the headset as of now
    // init();
    // END EMOTIV CODE
  }
});
