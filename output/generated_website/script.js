document.addEventListener('DOMContentLoaded', () => {
    // Smooth Scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Plank Challenge Timer
    let timer;
    let timeLeft = 60;
    const display = document.getElementById('timer-display');
    const startBtn = document.getElementById('start-timer');
    const resetBtn = document.getElementById('reset-timer');

    function updateDisplay() {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        display.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    startBtn.addEventListener('click', () => {
        if (timer) return; // Prevent multiple timers

        startBtn.disabled = true;
        startBtn.textContent = "Hold Plank!";

        timer = setInterval(() => {
            timeLeft--;
            updateDisplay();

            if (timeLeft <= 0) {
                clearInterval(timer);
                timer = null;
                display.textContent = "DONE!";
                display.style.color = "#ffff00"; // Yellow for finish
                startBtn.textContent = "Finished!";
            }
        }, 1000);
    });

    resetBtn.addEventListener('click', () => {
        clearInterval(timer);
        timer = null;
        timeLeft = 60;
        updateDisplay();
        display.style.color = "#e62b1e"; // Back to red
        startBtn.disabled = false;
        startBtn.textContent = "Start Challenge";
    });

    // Reveal animations on scroll
    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    document.querySelectorAll('.story-card, .booster-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease-out';
        observer.observe(el);
    });
});
