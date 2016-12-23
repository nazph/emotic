define([], function() {
  // This is used to open popup for headset
  function openPopup(selector) {
    $('.bpopup').each(function() {
      $(this).addClass('hidden');
    });
    $(selector).removeClass('hidden');
  }

  // This is used to close popup for headset
  function closePopup() {
    $('.bpopup').each(function() {
      $(this).addClass('hidden');
    });
    $('.bpopup-background').addClass('hidden');
  }
  return {
    openPopup: openPopup,
    closePopup: closePopup
  }
});
