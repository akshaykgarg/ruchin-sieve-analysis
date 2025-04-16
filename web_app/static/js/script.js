/**
 * Beach Sand Analysis Web App - Client-side JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // File input validation
    const fileInput = document.getElementById('sample_file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const filePath = this.value;
            const allowedExtensions = /(\.xlsx|\.xls)$/i;
            
            if (!allowedExtensions.exec(filePath)) {
                alert('Please upload Excel file (.xlsx or .xls)');
                this.value = '';
                return false;
            }
            
            // Show file name in the input
            const fileName = this.files[0].name;
            const fileNameDisplay = document.querySelector('.custom-file-label');
            if (fileNameDisplay) {
                fileNameDisplay.textContent = fileName;
            }
        });
    }
    
    // Delete confirmation modal setup
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const sampleId = button.getAttribute('data-sample-id');
            const sampleName = button.getAttribute('data-sample-name');
            
            const sampleNameElement = deleteModal.querySelector('#sampleName');
            if (sampleNameElement) {
                sampleNameElement.textContent = sampleName;
            }
            
            const deleteForm = deleteModal.querySelector('#deleteForm');
            if (deleteForm) {
                deleteForm.action = `/delete/${sampleId}`;
            }
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    if (forms.length > 0) {
        Array.from(forms).forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }
    
    // Table sorting functionality
    const sortableTables = document.querySelectorAll('.table-sortable');
    if (sortableTables.length > 0) {
        Array.from(sortableTables).forEach(function(table) {
            const headers = table.querySelectorAll('th[data-sort]');
            
            headers.forEach(function(header) {
                header.addEventListener('click', function() {
                    const column = this.dataset.sort;
                    const direction = this.dataset.direction || 'asc';
                    
                    // Reset all headers
                    headers.forEach(h => {
                        h.dataset.direction = '';
                        h.querySelector('i.sort-icon')?.remove();
                    });
                    
                    // Set direction for clicked header
                    this.dataset.direction = direction === 'asc' ? 'desc' : 'asc';
                    
                    // Add sort icon
                    const icon = document.createElement('i');
                    icon.className = `bi bi-sort-${direction === 'asc' ? 'down' : 'up'} ms-1 sort-icon`;
                    this.appendChild(icon);
                    
                    // Perform sort
                    sortTableByColumn(table, column, direction === 'asc');
                });
            });
        });
    }
    
    // Function to sort table
    function sortTableByColumn(table, column, ascending = true) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // Sort rows
        const sortedRows = rows.sort((a, b) => {
            const aValue = a.querySelector(`td:nth-child(${parseInt(column) + 1})`).textContent.trim();
            const bValue = b.querySelector(`td:nth-child(${parseInt(column) + 1})`).textContent.trim();
            
            // Check if values are numbers
            const aNum = parseFloat(aValue);
            const bNum = parseFloat(bValue);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return ascending ? aNum - bNum : bNum - aNum;
            }
            
            return ascending 
                ? aValue.localeCompare(bValue)
                : bValue.localeCompare(aValue);
        });
        
        // Clear table body
        while (tbody.firstChild) {
            tbody.removeChild(tbody.firstChild);
        }
        
        // Add sorted rows
        sortedRows.forEach(row => tbody.appendChild(row));
    }
    
    // Form reset confirmation
    const resetButtons = document.querySelectorAll('button[type="reset"]');
    if (resetButtons.length > 0) {
        resetButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to reset the form?')) {
                    e.preventDefault();
                }
            });
        });
    }
}); 