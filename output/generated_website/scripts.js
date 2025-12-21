document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    // Global settings for smooth scrolling and responsive considerations
    const initGlobalStyles = () => {
        try {
            document.documentElement.style.scrollBehavior = 'smooth';
        } catch (error) {
            console.error('Error setting global styles:', error);
        }
    };

    /**
     * Handles scrolling to a specific element by ID.
     * @param {string} targetId - The ID of the element to scroll to.
     */
    const handleScrollToElement = (targetId) => {
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            console.warn(`Scroll target element with ID "${targetId}" not found.`);
        }
    };

    /**
     * Handles navigation to a specific URL.
     * @param {string} url - The destination URL.
     */
    const handleNavigateToUrl = (url) => {
        if (url) {
            window.location.href = url;
        } else {
            console.error('Navigation URL is missing.');
        }
    };

    /**
     * Initializes Call to Action (CTA) event listeners.
     */
    const initCtaActions = () => {
        // Plank Challenge Button: Scroll to 'conclusion_challenge'
        const plankBtn = document.getElementById('plank_challenge_button');
        if (plankBtn) {
            plankBtn.addEventListener('click', (event) => {
                event.preventDefault();
                try {
                    handleScrollToElement('conclusion_challenge');
                } catch (error) {
                    console.error('Action failed: scroll_to_element', error);
                }
            });
        }

        // Learn More BDNF Button: Navigate to URL
        const bdnfBtn = document.getElementById('learn_more_bdnf_button');
        if (bdnfBtn) {
            bdnfBtn.addEventListener('click', (event) => {
                try {
                    handleNavigateToUrl('https://www.example.com/bdnf-research');
                } catch (error) {
                    console.error('Action failed: navigate_to_url', error);
                }
            });
        }
    };

    // Execution
    initGlobalStyles();
    initCtaActions();
});