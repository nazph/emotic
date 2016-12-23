/* global isConnected isThreeSensorsStatus openPopup closePopup isLostConnection
 EmoEngine EdkDll ELSPlugin timeConnection:true usernameCloud getReport
 define */

define(['loglevel',
'headset',
'helpers'], function(log, headset, helpers) {
  var isStartBaseline = false;
  var activityname;
  var interval;
  var baseline1 = false;
  var calibrationTime = 120;
  var baselineTime = calibrationTime / 2 * 1000;
  var baseline2 = false;
  var isEyeOpen = false;
  var isEyeClosed = false;
  var chunk = 0;
  var width = 0;
  var sampleNumber_EEG = 0;
  var countSampleEEG0 = 0;
  var countisOpenFileW = 0; // false
  var countisEEG = 0;
  var countCSVEmpty = 0; // =""
  var countisOpenFileR = 0; // -1
  var sampleNumber_Motion = 0;
  var sampleNumber_ES = 0;
  var eegDataFile;
  var	motionDataFile;
  var affectivDataFile;
  var isWriteHeader = false;
  var checkIntervalOut;
  var countOfFile = 0;
  var nameOfFile = '';

  $('#startBaseline').click(function() {
    helpers.openPopup('#baseline1');
     
    /* Allow the baseline to be accessed without the headset being connected
     * if (headset.isConnected) {
      if (isThreeSensorsStatus === true) {
        isStartBaseline = true;
        var progressBar1 = $('#baseline1_progress');
        progressBar1.width('0%');
        progressBar1.text("0%");
        var progressBar2 = $('#baseline2_progress');
        progressBar2.width('0%');
        progressBar2.text("0%");
        helpers.openPopup('#baseline1');
      } else {
        alert("Please adjust your Insight. " +
            "At least 3 sensors must be green to make a recording.");
        if (!isLostConnection) {
          timeConnection = new Date();
        }
      }
    } else {
      alert('Please connect headset to begin baseline.');
      if (!isLostConnection) timeConnection = new Date();
    }*/
  });

  // Click on Start in Baseline1
  $('#startEyesOpen').click(function() {
    isEyeOpen = true;
    baseline1 = true;
    var progressBar = $('#baseline1_progress');
    progressBar.width('0%');
    progressBar.text("0%");
    width = 0;
    $('#startEyesOpen').attr('disabled', 'disabled');
    $('#startEyesOpen').removeClass('highlightbutton');
    $('#startEyesOpen').addClass('cannot_click');
    fn_checkIntervalOut();
    log.debug('When start eyes open started EEG_sample:' +
        sampleNumber_EEG + ', ES sample:' + sampleNumber_ES);
    setTimeout(endTest1, baselineTime);
  });

  // Click on Cancel in Baseline1
  $('#cancelEyesOpen').click(function() {
    isStartBaseline = false;
    baseline1 = false;
    isEyeOpen = false;
    var progressBar = $('#baseline1_progress');
    progressBar.width('0%');
    progressBar.text("0%");
    $('#startEyesOpen').removeAttr('disabled');
    $('#startEyesOpen').css('opacity', 1);
    $('#startEyesOpen').removeClass('bp_btnclicked');
    $('#stp_recording').addClass('hidden');
    helpers.openPopup('#baseline');
    clearInterval(checkIntervalOut);
  });

  // Click on Start in Baseline2
  $('#startEyesClose').click(function() {
    baseline2 = true;
    isEyeClosed = true;
    var progressBar = $('#baseline2_progress');
    progressBar.width('0%');
    progressBar.text("0%");
    width = 0;
    $('#startEyesClose').attr('disabled', 'disabled');
    // $('#start_eyesclose').addClass('bp_btnclicked');
    $('#startEyesClose').removeClass('highlightbutton');
    $('#startEyesClose').addClass('cannot_click');
    fn_checkIntervalOut();
    setTimeout(endTest2, baselineTime);
  });

  // Click on Cancel in Baseline2
  $('#cancelEyesClose').click(function() {
    isStartBaseline = false;
    baseline2 = false;
    isEyeClosed = false;
    var progressBar1 = $('#baseline1_progress');
    progressBar1.width('0%');
    progressBar1.text("0%");
    var progressBar2 = $('#baseline2_progress');
    progressBar2.width('0%');
    progressBar2.text("0%");
    $('#startEyesClose').removeAttr('disabled');
    $('#startEyesOpen').removeAttr('disabled');
    $('#startEyesOpen').css('opacity', 1);
    $('#startEyesClose').css('opacity', 1);
    $('#startEyesClose').removeClass('bp_btnclicked');
    $('#startEeyesOpen').removeClass('bp_btnclicked');
    $('#stp_recording').addClass('hidden');
    helpers.openPopup('#baseline');
    clearInterval(checkIntervalOut);
    // delete data eeg, destroy session
  });

  function fn_checkIntervalOut() {
    if (nameOfFile === '') {
      nameOfFile = generateUUID();
    }
    log.debug("nameOfFile " + nameOfFile);
    checkIntervalOut = setInterval(function() {
      var today = new Date();
      var milliseconds = today.getMilliseconds();
      var timeStamp = Date.parse(today) / 1000 + milliseconds / 1000;
      var timeStampString = timeStamp.toString();
      if ((sampleNumber_EEG >= 23040 * countOfFile) &&
          (sampleNumber_EEG < 23040 * (countOfFile + 1))) {
        eegDataFile = nameOfFile + "_" + countOfFile + "_raw_eeg.csv";
        motionDataFile = nameOfFile + "_" + countOfFile + "_motion_eeg.csv";
        affectivDataFile = nameOfFile + "_" + countOfFile + "_affectiv_eeg.csv";
        countOfFile++;
      }
      //writeDatatoCSV(eegDataFile, motionDataFile,
          //affectivDataFile, timeStampString, isWriteHeader);
      if (!isWriteHeader) isWriteHeader = true;
      if (isEyeOpen) {
        width += 2;
        if (width < 100) {
          $('#baseline1_progress').text(width + "%");
          $('#baseline1_progress').width(width + '%');
        } else {
          $('#baseline1_progress').text("100%");
          $('#baseline1_progress').width('100%');
        }
      }
      if (isEyeClosed) {
        width += 2;
        if (width < 100) {
          $('#baseline2_progress').text(width + "%");
          $('#baseline2_progress').width(width + '%');
        } else {
          $('#baseline2_progress').text("100%");
          $('#baseline2_progress').width('100%');
        }
      }
    }, (baselineTime / 50));
  }

  function reject_recording() {
    if (confirm('Do you want to reject recording?')) {
      helpers.closePopup();
      $('#stp_recording').addClass('hidden');
      baseline1 = false;
      baseline2 = false;
    }
  }

  function accept_recording() {
    baseline1 = true;
    baseline2 = true;
    helpers.closePopup();
  }

  function stp_recordingbak() {
    isStartBaseline = false;
    clearInterval(checkIntervalOut);
    $('#start_baseline').css('pointer-events', 'auto');
    $('#start_baseline').css('opacity', '1');
    $('#stp_recording').addClass('hidden');
    $('#start_recording').removeClass('hidden');
    baseline1 = false;
    baseline2 = false;
    for (var i = 0; i < countOfFile; i++) {
      eegDataFile = encodeURIComponent(nameOfFile + "_" + i + "baseline_raw_eeg.csv");
      motionDataFile = encodeURIComponent(nameOfFile +
          "_" + i + "baseline_motion_eeg.csv");
      affectivDataFile = encodeURIComponent(nameOfFile +
          "_" + i + "baseline_affectiv_eeg.csv");
      var eegData = encodeURIComponent(ELSPlugin()
          .ELS_IEE_GetCSVDataBase64(eegDataFile));
      var motionData = encodeURIComponent(ELSPlugin()
          .ELS_IEE_GetCSVDataBase64(motionDataFile));
      var esData = encodeURIComponent(ELSPlugin()
          .ELS_IEE_GetCSVDataBase64(affectivDataFile));

      var functionid = 2;
      // log.debug("File i"+i);
      if (i === (countOfFile - 1)) {
        // log.debug('Ghi file cuoi cung');
        $.ajax({
          type: "POST",
          url: "/experiments/headset/post_data",
          data: "functionid=" + functionid +
            "&eegDataFile=" + eegDataFile +
            "&motionDataFile=" + motionDataFile +
            "&affectivDataFile=" + affectivDataFile +
            "&eegData=" + eegData +
            "&motionData=" + motionData +
            "&esData=" + esData +
            "&sampleEEG=" + sampleNumber_EEG +
            "&sampleES=" + sampleNumber_ES +
            "&countOfFile=" + countOfFile +
            "&nameOfFile=" + nameOfFile,
          success: function(html) {
            // log.debug("Zip file cuoi cung");
            functionid = 100;
            $.ajax({
              type: "POST",
              url: "post.php",
              data: "functionid=" + functionid +
                "&chunkOfFile=" + i +
                "&nameOfFile=" + nameOfFile,
              success: function(html) {
                // log.debug("Upload completed");
                $.ajax({
                  type: "POST",
                  url: "post.php",
                  data: "countOfFile=" + countOfFile +
                    "&completed=true&nameOfFile=" + nameOfFile,
                  success: function(html) {
                    countOfFile = 0;
                    nameOfFile = generateUUID();
                    sampleNumber_EEG = 0;
                    sampleNumber_ES = 0;
                    isWriteHeader = false;
                  }
                });
              }
            });
          }
        });
      } else {
        // log.debug("Ghi file thu"+i);
        // log.debug(eegDataFile + motionDataFile);
        $.ajax({
          type: "POST",
          url: "post.php",
          data: "functionid=" + functionid +
            "&eegDataFile=" + eegDataFile +
            "&motionDataFile=" + motionDataFile +
            "&affectivDataFile=" + affectivDataFile +
            "&eegData=" + eegData +
            "&motionData=" + motionData +
            "&esData=" + esData +
            "&sampleEEG=" + sampleNumber_EEG +
            "&sampleES=" + sampleNumber_ES +
            "&countOfFile=" + countOfFile +
            "&nameOfFile=" + nameOfFile,
          success: function(html) {
            // log.debug("Zip file thu" + i)
            functionid = 100;
            $.ajax({
              type: "POST",
              url: "post.php",
              data: "functionid=" + functionid +
                "&chunkOfFile=" + i +
                "&nameOfFile=" + nameOfFile
            });
          }
        });
      }
      var deleteEEGFile = ELSPlugin().ELS_IEE_DeleteCSVData(eegDataFile);
      var deleteMotionFile = ELSPlugin().ELS_IEE_DeleteCSVData(motionDataFile);
      var deleteAffectivFile = ELSPlugin()
        .ELS_IEE_DeleteCSVData(affectivDataFile);
    }

    /* 	log.debug("stop3");

      log.debug("stop4");
      setTimeout(function(){
      for(var i = 0; i < countOfFile; i++)
      {
      eegDataFile = encodeURIComponent(nameOfFile + "_" + i + "_raw_eeg.csv");
      motionDataFile = encodeURIComponent(nameOfFile + "_" + i + "_motion_eeg.csv");
      affectivDataFile = encodeURIComponent(nameOfFile + "_" + i + "_affectiv_eeg.csv");
      var deleteEEGFile = ELSPlugin().ELS_IEE_DeleteCSVData(eegDataFile);
      var deleteMotionFile = ELSPlugin().ELS_IEE_DeleteCSVData(motionDataFile);
      var deleteAffectivFile = ELSPlugin().ELS_IEE_DeleteCSVData(affectivDataFile);
      }
      $.ajax({
    type: "POST",
    url: "post.php",
    data: "countOfFile="+countOfFile+"&completed=true&nameOfFile="+nameOfFile,
    success: function(html)
    {
    countOfFile=0;
    nameOfFile=generateUUID();
    sampleNumber_EEG=0;
    sampleNumber_ES=0;
    isWriteHeader=false;
    }
    });
    },10000); */

    $('#activity_name').empty();
    helpers.openPopup('#generatesession');

    $('#startEyesOpen').removeAttr('disabled', 'disabled');
    $('#startEyesOpen').removeClass('cannot_click');
    $('#startEyesClose').removeAttr('disabled', 'disabled');
    $('#startEyesClose').removeClass('cannot_click');
  }

  function stp_recording() {
    var isLoadReportSessions = false;
    clearInterval(checkIntervalOut);
    $('#start_baseline').css('pointer-events', 'auto');
    $('#start_baseline').css('opacity', '1');
    $('#stp_recording').addClass('hidden');
    $('#start_recording').removeClass('hidden');
    baseline1 = false;
    baseline2 = false;

    for (var i = 0; i < countOfFile; i++) {
      eegDataFile = encodeURIComponent(nameOfFile +
          "_" + i + "_raw_eeg.csv");
      motionDataFile = encodeURIComponent(nameOfFile +
          "_" + i + "_motion_eeg.csv");
      affectivDataFile = encodeURIComponent(nameOfFile +
          "_" + i + "_affectiv_eeg.csv");
      var eegData = encodeURIComponent(ELSPlugin()
          .ELS_IEE_GetCSVDataBase64(eegDataFile));
      if (eegData === "-1") countisOpenFileR++;
      if (eegData === "") countCSVEmpty++;
      var motionData = encodeURIComponent(ELSPlugin()
          .ELS_IEE_GetCSVDataBase64(motionDataFile));
      var esData = encodeURIComponent(ELSPlugin()
          .ELS_IEE_GetCSVDataBase64(affectivDataFile));
      var functionid = 21;
      $.ajax({
          type: "POST",
          url: "/experiments/headset/post_data",
          data: "functionid=" + functionid +
            "&eegDataFile=" + eegDataFile +
            "&motionDataFile=" + motionDataFile +
            "&affectivDataFile=" + affectivDataFile +
            "&eegData=" + eegData +
            "&motionData=" + motionData +
            "&esData=" + esData +
            "&sampleEEG=" + sampleNumber_EEG +
            "&sampleES=" + sampleNumber_ES +
            "&countOfFile=" + countOfFile +
            "&nameOfFile=" + nameOfFile,
          success: function(data) {
          }
      });
    }
    log.debug("countSampleEEG0: " + countSampleEEG0);
    log.debug("countCSVEmpty: " + countCSVEmpty);
    log.debug("countisEEG: " + countisEEG);
    log.debug("countisOpenFileR: " + countisOpenFileR);
    log.debug("countisOpenFileW: " + countisOpenFileW);
    /* setTimeout(function(){
       for(var i = 0; i < countOfFile; i++)
       {
       eegDataFile = encodeURIComponent(nameOfFile + "_" + i + "_raw_eeg.csv");
       motionDataFile = encodeURIComponent(nameOfFile + "_" + i + "_motion_eeg.csv");
       affectivDataFile = encodeURIComponent(nameOfFile + "_" + i + "_affectiv_eeg.csv");
       var deleteEEGFile = ELSPlugin().ELS_IEE_DeleteCSVData(eegDataFile);
       var deleteMotionFile = ELSPlugin().ELS_IEE_DeleteCSVData(motionDataFile);
       var deleteAffectivFile = ELSPlugin().ELS_IEE_DeleteCSVData(affectivDataFile);
       }
       },1000); */

    countOfFile = 0;
    nameOfFile = generateUUID();
    sampleNumber_EEG = 0;
    countSampleEEG0 = 0;
    countCSVEmpty = 0;
    countisEEG = 0;
    countisOpenFileW = 0;
    countisOpenFileR = 0;
    sampleNumber_ES = 0;
    isWriteHeader = false;

    $('#activity_name').empty();
    helpers.openPopup('#generatesession');

    $('#startEyesOpen').removeAttr('disabled', 'disabled');
    $('#startEyesOpen').removeClass('cannot_click');
    $('#startEyesClose').removeAttr('disabled', 'disabled');
    $('#startEyesClose').removeClass('cannot_click');
  }

  function sendFlagCompleted() {
    $('#stp_recording').addClass('hidden');
    helpers.closePopup();

    setTimeout(function() {
      getReport();
    }, 90000);
  }

  function endTest1() {
    clearInterval(checkIntervalOut);
    isEyeOpen = false;
    $('#startEyesOpen').removeAttr('disabled');
    $('#startEyesOpen').css('opacity', 1);
    $('#startEyesOpen').removeClass('bp_btnclicked');
    log.debug(sampleNumber_EEG);
    log.debug(sampleNumber_ES);
    $('#baseline1').hide();
    setTimeout(function() {
      helpers.openPopup('#baseline2');
    }, 1000);
    var functionid = 5;
    /* $.ajax({
    type: "POST",
    url: "post.php",
    data: "functionid="+functionid+"&sampleEEG="+sampleNumber_EEG+"&sampleES="+sampleNumber_ES,

    });
    */
  }

  function endTest2() {
    clearInterval(checkIntervalOut);
    isEyeClosed = false;
    var snd = new Audio("/static/tone.wav");
    snd.play();
    $('#startEyesClose').removeAttr('disabled');
    $('#startEyesClose').css('opacity', 1);
    $('#startEyesClose').removeClass('bp_btnclicked');
    $('.content').hide();
    $('#experiment-view').show();
    setTimeout(function() {
      helpers.closePopup();
      helpers.openPopup('#basecomplete');
    }, 1000);

    var functionid = 7;
    /*
    $.ajax({
  type: "POST",
  url: "post.php",
  data: "functionid="+functionid+"&sampleEEG="+sampleNumber_EEG+"&sampleES="+sampleNumber_ES,

  });
  */
  }

function writeDatatoCSV(eegDataFile, motionDataFile, affectivDataFile, timeStamp, isWriteHeader)
{
		
		ELSPlugin().ELS_CreateDirectoryProfile("Emotiv", "Emotiv-EEG");
		EdkDll.IEE_DataUpdateHandle(0);
		var stringData = ELSPlugin().ELS_IEE_DataGetToFile(eegDataFile, timeStamp, isWriteHeader);
		var arrayEEGData = stringData.split(',');

		sampleNumber_EEG = sampleNumber_EEG + parseInt(arrayEEGData[1]);
		if(arrayEEGData[2]=="false")
			countisOpenFileW++;
		if(arrayEEGData[3]=="false")
			countisEEG++;
		if(sampleNumber_EEG==0)
			countSampleEEG0++;
		
		EdkDll.IEE_MotionDataUpdateHandle(0);
		var stringData = ELSPlugin().ELS_IEE_MotionDataGetToFile(motionDataFile, timeStamp, isWriteHeader);
		var arrayMotionData = stringData.split(',');
		sampleNumber_Motion = sampleNumber_Motion + parseInt(arrayMotionData[1]);
		if(sampleNumber_EEG > (sampleNumber_Motion + 60)) 
		{
			EdkDll.IEE_MotionDataUpdateHandle(0);
			var stringData = ELSPlugin().ELS_IEE_MotionDataGetToFile(motionDataFile, timeStamp, isWriteHeader);
			var arrayMotionData = stringData.split(',');
			sampleNumber_Motion = sampleNumber_Motion + parseInt(arrayMotionData[1]);
		}
		var stringData = ELSPlugin().ELS_IS_PerformanceMetricRawValueGetToFile(affectivDataFile, timeStamp, isWriteHeader);
		
		sampleNumber_ES++;
		if(sampleNumber_EEG > (sampleNumber_ES + 0.5) * 64) 
		{
			var stringData = ELSPlugin().ELS_IS_PerformanceMetricRawValueGetToFile(affectivDataFile, timeStamp, true);
			sampleNumber_ES++;
		}
}


  function StartEdk() {
    var enableDataAcqui = EdkDll.IEE_DataAcquisitionEnable(0, true);
    EdkDll.IEE_DataSetBufferSizeInSec(2);
    EdkDll.IEE_MotionDataSetBufferSizeInSec(2);
  }

  function generateUUID() {
    var d = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
      .replace(/[xy]/g, function(c) {
        var r = (d + Math.random() * 16) % 16 | 0;
        d = Math.floor(d / 16);
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
      });
    return uuid;
  }
  return {
    StartEdk: StartEdk
  };
  // refresh page session
});
