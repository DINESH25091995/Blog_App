function nextSlide(carouselId) {
    const carousel = document.getElementById(carouselId);
    const images = carousel.getElementsByClassName("carousel-image");
    let currentIndex = parseInt(carousel.getAttribute("data-index") || "0");

    if (currentIndex < images.length - 1) {
        currentIndex++;
    } else {
        currentIndex = 0; // Loop back to first image
    }

    carousel.style.transform = `translateX(-${currentIndex * 100}%)`;
    carousel.setAttribute("data-index", currentIndex);
}

function prevSlide(carouselId) {
    const carousel = document.getElementById(carouselId);
    const images = carousel.getElementsByClassName("carousel-image");
    let currentIndex = parseInt(carousel.getAttribute("data-index") || "0");

    if (currentIndex > 0) {
        currentIndex--;
    } else {
        currentIndex = images.length - 1; // Loop to last image
    }

    carousel.style.transform = `translateX(-${currentIndex * 100}%)`;
    carousel.setAttribute("data-index", currentIndex);
}
