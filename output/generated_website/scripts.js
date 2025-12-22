document.addEventListener('DOMContentLoaded', () => {
    /**
     * Smooth Scrolling Logic
     * Intercepts anchor links and scrolls smoothly to target sections.
     */
    const initSmoothScroll = () => {
        const anchors = document.querySelectorAll('a[href^="#"]');
        anchors.forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;

                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    };

    /**
     * Intersection Observer Logic
     * Adds 'visible' class to sections as they enter the viewport.
     */
    const initIntersectionObserver = () => {
        const sections = document.querySelectorAll('section');
        if (sections.length === 0) return;

        const options = {
            root: null,
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    // Optional: stop observing once visible
                    // observer.unobserve(entry.target);
                }
            });
        }, options);

        sections.forEach(section => {
            observer.observe(section);
        });
    };

    /**
     * Plank Timer Logic
     * Handles countdown, UI updates, and motivational messaging.
     */
    const initPlankTimer = () => {
        const startBtn = document.getElementById('start-btn');
        const resetBtn = document.getElementById('reset-btn');
        const display = document.getElementById('timer-display');
        const messageEl = document.querySelector('#challenge p');

        if (!startBtn || !resetBtn || !display || !messageEl) {
            console.warn('Plank timer elements not found in DOM.');
            return;
        }

        let timeLeft = 60;
        let timerId = null;

        const updateUI = () => {
            display.textContent = `${timeLeft}s`;

            if (timeLeft === 60) {
                messageEl.textContent = "Ready? Get into position!";
            } else if (timeLeft === 30) {
                messageEl.textContent = "Halfway there! Keep your core tight!";
            } else if (timeLeft === 10) {
                messageEl.textContent = "Almost done! Final push!";
            } else if (timeLeft === 0) {
                messageEl.textContent = "Victory! Challenge complete.";
            }
        };

        const startTimer = () => {
            if (timerId !== null) return; // Prevent multiple intervals

            timerId = setInterval(() => {
                timeLeft--;
                updateUI();

                if (timeLeft <= 0) {
                    clearInterval(timerId);
                    timerId = null;
                }
            }, 1000);
        };

        const resetTimer = () => {
            clearInterval(timerId);
            timerId = null;
            timeLeft = 60;
            updateUI();
        };

        startBtn.addEventListener('click', startTimer);
        resetBtn.addEventListener('click', resetTimer);
    };

    // Initialize all features within a try-catch for graceful error handling
    try {
        initSmoothScroll();
        initIntersectionObserver();
        initPlankTimer();
    } catch (error) {
        console.error('An error occurred while initializing interactions:', error);
    }
});