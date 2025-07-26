// app/static/js/welcome.js

document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('welcome-modal');
  const closeModalBtn = document.getElementById('close-welcome-modal');

  // If the modal doesn't exist on the page, do nothing.
  if (!modal || !closeModalBtn) {
    return;
  }

  // Check sessionStorage to see if the modal has already been shown in this session.
  if (!sessionStorage.getItem('welcomeModalShown')) {
    // If not shown, remove the 'hidden' class to display it.
    modal.classList.remove('hidden');
    // Set a flag in sessionStorage so it doesn't show again on subsequent page loads.
    sessionStorage.setItem('welcomeModalShown', 'true');
  }

  // Event listener for the close button.
  closeModalBtn.addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  // Optional: Add event listener to close the modal if the user clicks on the background overlay.
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.add('hidden');
    }
  });
});
