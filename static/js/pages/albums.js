/* Albums page JS - cover image preview */
document.addEventListener('DOMContentLoaded', function () {
  var input = document.getElementById('id_cover_image');
  var preview = document.getElementById('cover-preview');
  var img = preview ? preview.querySelector('img') : null;
  if (input && preview && img) {
    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      if (file) {
        img.src = URL.createObjectURL(file);
        preview.classList.remove('hidden');
      } else {
        preview.classList.add('hidden');
      }
    });
  }
});
