document.addEventListener('DOMContentLoaded', () => {
    const welcomeModal = document.getElementById('welcomeModal');
    const modalContent = document.getElementById('modalContent');
    const closeModalBtn = document.getElementById('closeModal');
    const exploreMapBtn = document.getElementById('exploreMapBtn');
    
    // NEW: Get the info button from the navbar
    const showWelcomeBtn = document.getElementById('showWelcomeBtn');

    // Function to show the modal with animation
    function showModal() {
        if (welcomeModal && modalContent) {
            welcomeModal.classList.remove('hidden');
            setTimeout(() => {
                modalContent.classList.remove('scale-95', 'opacity-0');
            }, 10);
        }
    }

    // Function to hide the modal with animation
    function hideModal() {
        if (welcomeModal && modalContent) {
            modalContent.classList.add('scale-95', 'opacity-0');
            setTimeout(() => {
                welcomeModal.classList.add('hidden');
            }, 200);
        }
    }

    // Show modal on first visit of the session
    if (!sessionStorage.getItem('welcomeShown')) {
        // Add a small delay for a smoother entry on page load
        setTimeout(showModal, 500);
        sessionStorage.setItem('welcomeShown', 'true');
    }

    // Event listeners to close the modal
    if (closeModalBtn) closeModalBtn.addEventListener('click', hideModal);
    if (exploreMapBtn) exploreMapBtn.addEventListener('click', hideModal);

    // NEW: Event listener for the navbar info button to show the modal
    if (showWelcomeBtn) {
        showWelcomeBtn.addEventListener('click', showModal);
    }
});
