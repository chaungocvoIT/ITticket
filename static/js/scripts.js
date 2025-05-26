document.addEventListener('DOMContentLoaded', function() {
    // Basic form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
            let valid = true;
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    input.style.border = '1px solid red';
                } else {
                    input.style.border = '';
                }
            });
            if (!valid) {
                event.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });

    // Confirm ticket closure
    const closeButtons = document.querySelectorAll('select[name="action_type"]');
    closeButtons.forEach(select => {
        select.addEventListener('change', function() {
            if (this.value === 'Close') {
                if (!confirm('Are you sure you want to close this ticket?')) {
                    this.value = '';
                }
            }
        });
    });
});