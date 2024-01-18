window.addEventListener('DOMContentLoaded', (event) => {
    // Elements
    const dropZone = document.querySelector(".drop-zone");
    const fileInput = document.querySelector("#file-input");
    const uploadButton = document.getElementById('uploadButton');
    const visualizeButton = document.getElementById('visualizeButton');
    const loading = document.getElementById('loading');
  
    // Drag-and-drop functionality
    dropZone.addEventListener("dragover", (event) => {
      event.preventDefault();
      dropZone.classList.add("dragover");
    });
  
    dropZone.addEventListener("dragleave", (event) => {
      event.preventDefault();
      dropZone.classList.remove("dragover");
    });
  
    dropZone.addEventListener("drop", (event) => {
      event.preventDefault();
      dropZone.classList.remove("dragover");
      fileInput.files = event.dataTransfer.files;
      uploadButton.click(); // Automatically trigger upload
    });
  
    // Form submission handling
    uploadButton.onclick = function() {
      const form = document.getElementById('uploadForm');
      const formData = new FormData(form);
  
      loading.style.display = 'block'; // Show loading indicator
  
      fetch('/summarize', {
        method: 'POST',
        body: formData,
      })
      .then(response => response.json())
      .then(data => {
        console.log(data.summary); // Log summary to the browser console
        // Handle the summary data as needed, e.g., display it on the page
        loading.style.display = 'none'; // Hide loading indicator
      })
      .catch(error => {
        console.error('Error during summarization:', error);
        loading.style.display = 'none'; // Hide loading indicator
      });
    };
  
    // Visualize button handling
    if (visualizeButton) {
      visualizeButton.onclick = function() {
        generateAndDisplayChart();
      };
    }
  });
  
