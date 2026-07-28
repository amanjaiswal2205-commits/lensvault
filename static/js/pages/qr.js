/* QR detail page JS - copy button */
document.addEventListener('DOMContentLoaded', function () {
  var copyBtn = document.getElementById('copy-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var input = document.getElementById('access-link');
      if (input && navigator.clipboard) {
        navigator.clipboard.writeText(input.value).then(function () {
          var original = copyBtn.textContent;
          copyBtn.textContent = 'Copied!';
          setTimeout(function () { copyBtn.textContent = original; }, 1500);
        });
      }
    });
  }
});
