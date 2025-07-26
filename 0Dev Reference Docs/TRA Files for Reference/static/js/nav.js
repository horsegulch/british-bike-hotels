document.addEventListener('DOMContentLoaded', function() {
    
console.log('CONFIRMED: nav.js script is now running!');

    const hamburgerButton = document.getElementById('hamburger-button');
    const mobileNav = document.getElementById('mobile-nav');

    if (hamburgerButton && mobileNav) {
        hamburgerButton.addEventListener('click', function() {
            // Toggle the 'is-open' class on both the button and the menu
            hamburgerButton.classList.toggle('is-open');
            mobileNav.classList.toggle('is-open');
        });
    }
});