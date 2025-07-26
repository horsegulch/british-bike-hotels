document.addEventListener('DOMContentLoaded', function () {
    // --- Element Selection ---
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');
    const uploadForm = document.getElementById('uploadForm');
    const urlForm = document.getElementById('urlForm');
    const loadingDiv = document.getElementById('loading');
    const errorOutputDiv = document.getElementById('errorOutput');
    const dropZone = document.getElementById('dropZone');
    const gpxFileInput = document.getElementById('gpxFile');
    const browseLink = document.getElementById('browseLink');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const glossaryToggle = document.querySelector('.glossary-toggle');
    const glossaryContent = document.querySelector('.glossary-content');

    // --- Tab Switching Logic ---
    tabLinks.forEach(link => {
        link.addEventListener('click', () => {
            const tabId = link.getAttribute('data-tab');
            tabLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            link.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // --- Drag and Drop Logic ---
    if (dropZone) {
        browseLink.addEventListener('click', (e) => { e.preventDefault(); gpxFileInput.click(); });
        dropZone.addEventListener('click', () => { gpxFileInput.click(); });
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
        });
        dropZone.addEventListener('drop', (e) => { gpxFileInput.files = e.dataTransfer.files; displayFileNames(); }, false);
        gpxFileInput.addEventListener('change', displayFileNames);
        function displayFileNames() {
            if (gpxFileInput.files.length > 0) {
                const names = Array.from(gpxFileInput.files).map(f => f.name).join(', ');
                fileNameDisplay.textContent = `Selected: ${names}`;
            } else {
                fileNameDisplay.textContent = '';
            }
        }
    }

    // --- Glossary Toggle Logic ---
    if (glossaryToggle) {
        glossaryToggle.addEventListener('click', () => {
            glossaryToggle.classList.toggle('open');
            glossaryContent.style.display = glossaryToggle.classList.contains('open') ? 'block' : 'none';
        });
    }

    // --- UNIFIED ASYNCHRONOUS SUBMISSION LOGIC ---
    if (uploadForm) {
        uploadForm.addEventListener('submit', function (e) {
            e.preventDefault();
            if (!gpxFileInput.files.length) {
                showError('Please select a file to upload.');
                return;
            }
            const formData = new FormData();
            formData.append('gpx_file', gpxFileInput.files[0]);
            const fetchPromise = fetch('/process_route_file', { method: 'POST', body: formData });
            startTask(fetchPromise, this.querySelector('button[type="submit"]'));
        });
    }

    if (urlForm) {
        urlForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const routeURL = document.getElementById('routeUrl').value.trim();
            if (!routeURL) {
                showError('Please enter a route URL.');
                return;
            }
            const fetchPromise = fetch('/process_route_url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ route_url: routeURL })
            });
            startTask(fetchPromise, this.querySelector('button[type="submit"]'));
        });
    }

    function startTask(fetchPromise, submitButton) {
        submitButton.disabled = true;
        clearFeedback();
        loadingDiv.style.display = 'block';
        loadingDiv.textContent = 'Submitting job to be processed...';

        fetchPromise
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.error || 'Submission failed.') });
                }
                return response.json();
            })
            .then(data => {
                if (data.task_id) {
                    loadingDiv.textContent = 'Job received. Processing route... This may take a moment.';
                    pollTaskStatus(data.task_id, submitButton);
                } else {
                    throw new Error(data.error || 'Failed to start task.');
                }
            })
            .catch(error => {
                showError(`Submission Error: ${error.message}`);
                submitButton.disabled = false;
            });
    }

    function pollTaskStatus(taskId, submitButton) {
        const interval = setInterval(() => {
            fetch(`/task_status/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    console.log('Received success data from server:', data);
                    if (data.state === 'SUCCESS') {


                        clearInterval(interval);
                        const draftId = data.result.draft_id;
                        loadingDiv.textContent = 'Processing complete! Redirecting...';
                        window.location.href = `/publish/${draftId}`;
                    } else if (data.state === 'FAILURE') {
                        clearInterval(interval);
                        showError(`Error during processing: ${data.status}`);
                        submitButton.disabled = false;
                    }
                })
                .catch(error => {
                    clearInterval(interval);
                    showError(`Error checking status: ${error.message}`);
                    submitButton.disabled = false;
                });
        }, 3000); // Poll every 3 seconds
    }

    // --- Helper Functions ---
    function clearFeedback() {
        errorOutputDiv.innerHTML = '';
        loadingDiv.style.display = 'none';
        loadingDiv.textContent = 'Processing, please wait...'; // Reset text
    }

    function showError(message) {
        loadingDiv.style.display = 'none';
        errorOutputDiv.innerHTML = `<p style="color:red;">${message}</p>`;
    }
});