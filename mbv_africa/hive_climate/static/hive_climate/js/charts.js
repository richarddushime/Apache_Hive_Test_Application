// Tab Navigation
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(tabName).classList.add('active');
    
    // Add active class to clicked button
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Initialize charts if needed
    if (tabName === 'trends' && typeof initializeTrendsCharts === 'function') {
        setTimeout(initializeTrendsCharts, 100);
    }
}

// Initialize default tab on load
document.addEventListener('DOMContentLoaded', function() {
    switchTab('schema');
    
    // Initialize Chart.js if available
    if (typeof Chart !== 'undefined') {
        // Charts will be initialized by individual tab scripts
    }
});
