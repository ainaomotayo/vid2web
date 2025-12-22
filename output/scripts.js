document.addEventListener('DOMContentLoaded', () => {
    try {
        /**
         * Smooth Scroll Interaction
         * Targets: nav a
         */
        const navLinks = document.querySelectorAll('nav a');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (event) => {
                const targetId = link.getAttribute('href');
                
                // Only handle internal anchor links
                if (targetId && targetId.startsWith('#')) {
                    event.preventDefault();
                    
                    const targetElement = document.querySelector(targetId);
                    if (targetElement) {
                        targetElement.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }
            });
        });

        /**
         * fadeInUp Animation Interaction
         * Target: section
         * Trigger: intersection
         * Duration: 0.5s
         */
        const sections = document.querySelectorAll('section');
        
        if ('IntersectionObserver' in window) {
            const animationOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const intersectionCallback = (entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        element.style.opacity = '1';
                        element.style.transform = 'translateY(0)';
                        observer.unobserve(element);
                    }
                });
            };

            const observer = new IntersectionObserver(intersectionCallback, animationOptions);

            sections.forEach(section => {
                // Set initial state for fadeInUp
                section.style.opacity = '0';
                section.style.transform = 'translateY(20px)';
                section.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
                section.style.willChange = 'transform, opacity';
                
                observer.observe(section);
            });
        } else {
            // Fallback for older browsers
            sections.forEach(section => {
                section.style.opacity = '1';
                section.style.transform = 'translateY(0)';
            });
        }

    } catch (error) {
        console.error('Error initializing site interactions:', error);
    }
});