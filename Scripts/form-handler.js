// Submits every .form-card form to Web3Forms via fetch so the visitor
// stays on the page instead of navigating to Web3Forms' hosted response.
(function () {
  function handleSubmit(form) {
    var button = form.querySelector('button[type="submit"]');
    var originalText = button.textContent;

    var status = document.createElement('p');
    status.className = 'form-status';
    form.appendChild(status);

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      button.disabled = true;
      button.textContent = 'Sending...';
      status.textContent = '';
      status.className = 'form-status';

      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' },
      })
        .then(function (response) {
          return response.json();
        })
        .then(function (data) {
          if (data.success) {
            form.reset();
            status.textContent =
              "Thanks — we've received your request and will be in touch shortly.";
            status.classList.add('form-status--success');
          } else {
            throw new Error(data.message || 'Submission failed');
          }
        })
        .catch(function () {
          status.textContent =
            'Something went wrong sending your request. Please call us at (281) 221-5993 instead.';
          status.classList.add('form-status--error');
        })
        .finally(function () {
          button.disabled = false;
          button.textContent = originalText;
        });
    });
  }

  document.querySelectorAll('form.form-card').forEach(handleSubmit);
})();
