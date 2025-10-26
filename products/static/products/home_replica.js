// Very small carousel: cycles through .slide elements inside #carousel
document.addEventListener('DOMContentLoaded', function () {
    var carousel = document.getElementById('carousel');
    if (!carousel) return;

    var slides = carousel.querySelectorAll('.slide');
    var dotsContainer = document.getElementById('carousel-dots');
    var prevBtn = document.getElementById('carousel-prev');
    var nextBtn = document.getElementById('carousel-next');
    var idx = 0;
    var interval = null;

    function show(i) {
        slides.forEach(function (s, j) {
            s.style.display = j === i ? 'block' : 'none';
            s.setAttribute('aria-hidden', j === i ? 'false' : 'true');
        });
        // update dots
        if (dotsContainer) {
            Array.from(dotsContainer.children).forEach(function (d, j) {
                d.classList.toggle('bg-gray-800', j === i);
                d.classList.toggle('bg-gray-400', j !== i);
                d.setAttribute('aria-current', j === i ? 'true' : 'false');
            });
        }
        idx = i;
    }

    // initialize
    slides.forEach(function (s, i) { if (i !== 0) s.style.display = 'none'; s.setAttribute('aria-hidden', i === 0 ? 'false' : 'true'); });

    // create dots
    if (dotsContainer) {
        slides.forEach(function (_, i) {
            var dot = document.createElement('button');
            dot.className = 'w-3 h-3 rounded-full bg-gray-400';
            dot.setAttribute('aria-label', 'Go to slide ' + (i + 1));
            dot.setAttribute('aria-current', i === 0 ? 'true' : 'false');
            dot.addEventListener('click', function () { show(i); resetInterval(); });
            dotsContainer.appendChild(dot);
        });
    }

    function next() { show((idx + 1) % slides.length); }
    function prev() { show((idx - 1 + slides.length) % slides.length); }

    if (nextBtn) nextBtn.addEventListener('click', function () { next(); resetInterval(); });
    if (prevBtn) prevBtn.addEventListener('click', function () { prev(); resetInterval(); });

    // keyboard
    carousel.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') { prev(); resetInterval(); }
        if (e.key === 'ArrowRight') { next(); resetInterval(); }
    });
    carousel.setAttribute('tabindex', '0');

    function resetInterval() {
        if (interval) clearInterval(interval);
        interval = setInterval(next, 4000);
    }

    // start autoplay
    interval = setInterval(next, 4000);
});