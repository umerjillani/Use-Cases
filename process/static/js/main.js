/**
 * Main JavaScript for Intelligent Document Processing System
 */

// Global variables
let documentsChart = null;
let exceptionsChart = null;

/**
 * Initialize dashboard data and charts
 */
function initDashboard() {
    // Fetch dashboard statistics
    fetch('/api/dashboard/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch dashboard statistics');
            }
            return response.json();
        })
        .then(data => {
            updateDashboardStats(data);
            initCharts(data);
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Error loading dashboard data', 'danger');
        });
    
    // Fetch recent activity
    fetch('/api/dashboard/recent-activity')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch recent activity');
            }
            return response.json();
        })
        .then(data => {
            updateRecentActivity(data);
        })
        .catch(error => {
            console.error('Error:', error);
            // Don't show a toast for this, just log it
        });
}

/**
 * Update dashboard statistics
 * @param {Object} data - Dashboard statistics data
 */
function updateDashboardStats(data) {
    // Update quick stats
    if (data.documents) {
        document.getElementById('total-documents').textContent = data.documents.total || 0;
        document.getElementById('valid-documents').textContent = data.documents.valid || 0;
    }
    
    if (data.batches) {
        document.getElementById('total-batches').textContent = data.batches.total || 0;
        
        // Update batch amount stats
        const totalProcessedAmount = data.batches.total_amount || 0;
        const totalVerifiedAmount = data.batches.total_verified_amount || 0;
        const amountVariance = Math.abs(totalProcessedAmount - totalVerifiedAmount);
        
        document.getElementById('total-processed-amount').textContent = formatCurrency(totalProcessedAmount);
        document.getElementById('total-verified-amount').textContent = formatCurrency(totalVerifiedAmount);
        document.getElementById('amount-variance').textContent = formatCurrency(amountVariance);
        
        // Add color coding for variance
        const varianceElement = document.getElementById('amount-variance');
        if (amountVariance > 0) {
            varianceElement.classList.remove('text-success');
            varianceElement.classList.add('text-danger');
        } else {
            varianceElement.classList.remove('text-danger');
            varianceElement.classList.add('text-success');
        }
    }
    
    if (data.exceptions) {
        const openExceptions = data.exceptions.by_status?.open || 0;
        document.getElementById('open-exceptions').textContent = openExceptions;
    }
}

/**
 * Initialize charts with dashboard data
 * @param {Object} data - Dashboard statistics data
 */
function initCharts(data) {
    // Documents by Type chart
    const documentTypeCtx = document.getElementById('documents-by-type-chart');
    if (documentTypeCtx && data.documents?.by_type) {
        const labels = Object.keys(data.documents.by_type);
        const values = Object.values(data.documents.by_type);
        
        // Define colors for document types
        const backgroundColors = [
            '#0d6efd', // primary - blue
            '#198754', // success - green
            '#ffc107', // warning - yellow
            '#dc3545', // danger - red
            '#6c757d', // secondary - gray
            '#0dcaf0', // info - light blue
            '#6610f2', // purple
            '#fd7e14'  // orange
        ];
        
        // Destroy existing chart if it exists
        if (documentsChart) {
            documentsChart.destroy();
        }
        
        // Create new chart
        documentsChart = new Chart(documentTypeCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: backgroundColors.slice(0, labels.length),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 15,
                            padding: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Exceptions by Severity chart
    const exceptionSeverityCtx = document.getElementById('exceptions-by-severity-chart');
    if (exceptionSeverityCtx && data.exceptions?.by_severity) {
        const labels = Object.keys(data.exceptions.by_severity);
        const values = Object.values(data.exceptions.by_severity);
        
        // Define colors for exception severities
        const backgroundColors = {
            'info': '#0dcaf0',    // info - light blue
            'warning': '#ffc107', // warning - yellow
            'error': '#dc3545'    // danger - red
        };
        
        // Map labels to colors
        const colors = labels.map(label => backgroundColors[label] || '#6c757d');
        
        // Destroy existing chart if it exists
        if (exceptionsChart) {
            exceptionsChart.destroy();
        }
        
        // Create new chart
        exceptionsChart = new Chart(exceptionSeverityCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Exception Count',
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
}

/**
 * Update recent activity tables
 * @param {Object} data - Recent activity data
 */
function updateRecentActivity(data) {
    // Update recent documents table
    const documentsTable = document.getElementById('recent-documents-table');
    if (documentsTable && data.documents) {
        if (data.documents.length === 0) {
            documentsTable.innerHTML = '<tr><td colspan="4" class="text-center">No documents found</td></tr>';
        } else {
            documentsTable.innerHTML = '';
            data.documents.forEach(doc => {
                const statusClass = `status-${doc.status}`;
                documentsTable.innerHTML += `
                    <tr>
                        <td>${doc.id}</td>
                        <td>${doc.filename}</td>
                        <td>${formatDocumentType(doc.document_type)}</td>
                        <td><span class="status-badge ${statusClass}">${doc.status}</span></td>
                    </tr>
                `;
            });
        }
    }
    
    // Update recent exceptions table
    const exceptionsTable = document.getElementById('recent-exceptions-table');
    if (exceptionsTable && data.exceptions) {
        if (data.exceptions.length === 0) {
            exceptionsTable.innerHTML = '<tr><td colspan="4" class="text-center">No exceptions found</td></tr>';
        } else {
            exceptionsTable.innerHTML = '';
            data.exceptions.forEach(ex => {
                const statusClass = `status-${ex.status}`;
                const severityClass = `severity-${ex.severity}`;
                exceptionsTable.innerHTML += `
                    <tr class="${severityClass}">
                        <td>${ex.id}</td>
                        <td>${ex.exception_type}</td>
                        <td>${truncateText(ex.message, 50)}</td>
                        <td><span class="status-badge ${statusClass}">${ex.status}</span></td>
                    </tr>
                `;
            });
        }
    }
}

/**
 * Format document type for display
 * @param {string} type - Document type
 * @returns {string} Formatted document type
 */
function formatDocumentType(type) {
    if (!type) return 'Unknown';
    
    // Convert snake_case to Title Case
    return type
        .replace(/_/g, ' ')
        .replace(/\w\S*/g, text => text.charAt(0).toUpperCase() + text.substr(1).toLowerCase());
}

/**
 * Truncate text to a maximum length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {string} type - Toast type (success, danger, warning, info)
 */
function showToast(message, type = 'info') {
    // Check if toast container exists, if not create it
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast show bg-${type} text-white`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">System Notification</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Auto-remove toast after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Format currency for display
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
    if (amount === undefined || amount === null) return '$0.00';
    return '$' + parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

/**
 * Add event listeners to page elements
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add global event listeners here
    
    // Example: Upload form submit handler
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // Handle form submission
            const formData = new FormData(uploadForm);
            uploadDocument(formData);
        });
    }
    
    // Example: Batch create form submit handler
    const batchForm = document.getElementById('batch-form');
    if (batchForm) {
        batchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // Handle form submission
            const formData = new FormData(batchForm);
            createBatch(formData);
        });
    }
});

/**
 * Upload a document
 * @param {FormData} formData - Form data with file and document type
 */
function uploadDocument(formData) {
    // Show loading indicator
    showToast('Uploading document...', 'info');
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to upload document');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showToast('Document uploaded successfully', 'success');
            // Optionally redirect to document page
            // window.location.href = `/documents/${data.document_id}`;
        } else {
            showToast(data.message || 'Upload failed', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error uploading document', 'danger');
    });
}

/**
 * Create a batch
 * @param {FormData} formData - Form data with batch details
 */
function createBatch(formData) {
    // Convert FormData to JSON
    const batchData = {};
    formData.forEach((value, key) => {
        batchData[key] = value;
    });
    
    // Extract document IDs if present
    if (formData.has('document_ids')) {
        const documentIds = formData.getAll('document_ids');
        batchData.document_ids = documentIds.map(id => parseInt(id));
    }
    
    // Show loading indicator
    showToast('Creating batch...', 'info');
    
    fetch('/api/batches', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(batchData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to create batch');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showToast('Batch created successfully', 'success');
            // Optionally redirect to batch page
            // window.location.href = `/batches/${data.batch.id}`;
        } else {
            showToast(data.message || 'Batch creation failed', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error creating batch', 'danger');
    });
}