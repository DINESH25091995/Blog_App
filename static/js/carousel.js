// JavaScript for handling carousel slide movement
function prevSlide(carouselId) {
    const carousel = document.getElementById(carouselId);
    const firstItem = carousel.querySelector('img');
    const lastItem = carousel.lastElementChild;
    carousel.insertBefore(lastItem, firstItem);
}

function nextSlide(carouselId) {
    const carousel = document.getElementById(carouselId);
    const firstItem = carousel.querySelector('img');
    const lastItem = carousel.lastElementChild;
    carousel.appendChild(firstItem);
}
