/**
 * Lightbox xem screenshot o kich thuoc lon.
 *
 * Cach dung trong HTML: dat thuoc tinh data-lightbox len the <img> bat ky.
 * Script tu gan su kien, tu tao lop phu — khong can markup them.
 *
 * Neu tat JavaScript: anh van hien binh thuong trong luoi, chi mat phan phong to.
 */
(function () {
  'use strict';

  var images = Array.prototype.slice.call(
    document.querySelectorAll('img[data-lightbox]')
  );
  if (images.length === 0) return;

  var currentIndex = 0;

  // --- Dung lop phu ------------------------------------------------------

  var overlay = document.createElement('div');
  overlay.className = 'lightbox';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', 'Xem anh phong to');

  var fullImage = document.createElement('img');
  fullImage.className = 'lightbox__image';
  overlay.appendChild(fullImage);

  var closeButton = document.createElement('button');
  closeButton.type = 'button';
  closeButton.setAttribute('aria-label', 'Dong');
  closeButton.className =
    'absolute top-5 right-5 text-white/70 hover:text-white transition-colors ' +
    'duration-200 cursor-pointer text-3xl leading-none';
  closeButton.innerHTML = '&times;';
  overlay.appendChild(closeButton);

  document.body.appendChild(overlay);

  // --- Dieu khien --------------------------------------------------------

  function open(index) {
    currentIndex = index;
    var source = images[index];
    fullImage.src = source.currentSrc || source.src;
    fullImage.alt = source.alt;
    overlay.dataset.open = 'true';
    document.body.dataset.lightboxOpen = 'true';
    closeButton.focus();
  }

  function close() {
    overlay.dataset.open = 'false';
    document.body.dataset.lightboxOpen = 'false';
    // Tra focus ve dung anh vua xem de nguoi dung ban phim khong bi mat cho.
    images[currentIndex].focus();
  }

  function step(delta) {
    open((currentIndex + delta + images.length) % images.length);
  }

  // --- Gan su kien -------------------------------------------------------

  images.forEach(function (image, index) {
    image.tabIndex = 0;
    image.setAttribute('role', 'button');
    image.classList.add('cursor-pointer');

    image.addEventListener('click', function () {
      open(index);
    });
    image.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        open(index);
      }
    });
  });

  closeButton.addEventListener('click', close);

  // Bam ra vung nen (khong phai anh) thi dong.
  overlay.addEventListener('click', function (event) {
    if (event.target === overlay) close();
  });

  document.addEventListener('keydown', function (event) {
    if (overlay.dataset.open !== 'true') return;
    if (event.key === 'Escape') close();
    if (event.key === 'ArrowRight') step(1);
    if (event.key === 'ArrowLeft') step(-1);
  });
})();
