/**
 * BizFlow Quick-Add & Form State Preservation Engine
 * Allows inline modal creation of Companies, Customers, Suppliers, Products, Categories,
 * without ever losing form data or reloading the active page.
 */

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const getCsrfToken = () => {
  const input = document.querySelector('[name=csrfmiddlewaretoken]');
  return input ? input.value : getCookie('csrftoken') || '';
};

function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '99999';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.gap = '10px';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.style.minWidth = '260px';
  toast.style.maxWidth = '420px';
  toast.style.boxShadow = '0 6px 16px rgba(0,0,0,0.12)';
  toast.style.borderRadius = '6px';
  toast.style.padding = '12px 16px';
  toast.style.display = 'flex';
  toast.style.alignItems = 'center';
  toast.style.justifyContent = 'space-between';
  toast.style.backgroundColor = type === 'success' ? '#10B981' : (type === 'danger' ? '#EF4444' : '#3B82F6');
  toast.style.color = '#FFFFFF';
  toast.style.fontWeight = '500';
  toast.style.fontSize = '14px';
  toast.style.transition = 'all 0.3s ease';

  toast.innerHTML = `
    <span>${message}</span>
    <button type="button" style="background:transparent; border:none; color:#FFF; font-size:18px; cursor:pointer; margin-left:12px; line-height:1;" onclick="this.parentElement.remove()">&times;</button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function openQuickModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  const firstInput = modal.querySelector('input:not([type=hidden]), select, textarea');
  if (firstInput) firstInput.focus();
}

function closeQuickModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.style.display = 'none';
  document.body.style.overflow = '';
}

// Global ESC key listener for modals
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.quick-modal').forEach((m) => {
      m.style.display = 'none';
    });
    document.body.style.overflow = '';
  }
});

/**
 * Submits an inline modal form via AJAX, adds the created object to the target dropdown,
 * selects it, and closes the modal without page reload.
 */
function submitQuickForm(event, form, targetSelectId, modalId, callback) {
  event.preventDefault();
  const submitBtn = form.querySelector('button[type=submit]');
  const origBtnText = submitBtn ? submitBtn.innerHTML : 'Save';
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = 'Saving...';
  }

  const errorBox = form.querySelector('.quick-form-errors');
  if (errorBox) {
    errorBox.style.display = 'none';
    errorBox.innerHTML = '';
  }

  const formData = new FormData(form);

  fetch(form.action, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: formData
  })
  .then(async (response) => {
    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.message || (data.errors ? JSON.stringify(data.errors) : 'Failed to save. Please check input.'));
    }
    return data;
  })
  .then((data) => {
    // 1. Add to target select
    const select = document.getElementById(targetSelectId);
    if (select) {
      // Check if option already exists
      let option = select.querySelector(`option[value="${data.id}"]`);
      if (!option) {
        option = document.createElement('option');
        option.value = data.id;
        option.textContent = data.name;
        select.appendChild(option);
      }
      select.value = data.id;
      // Trigger change event for listeners
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // 2. Success feedback
    showToast(data.message || `${data.name} created and selected!`, 'success');

    // 3. Reset form and close modal
    form.reset();
    closeQuickModal(modalId);

    if (typeof callback === 'function') {
      callback(data);
    }
  })
  .catch((err) => {
    if (errorBox) {
      errorBox.style.display = 'block';
      errorBox.innerHTML = `<div class="alert alert-danger" style="margin-bottom:12px; font-size:13px;">${err.message}</div>`;
    } else {
      showToast(err.message, 'danger');
    }
  })
  .finally(() => {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = origBtnText;
    }
  });
}

/**
 * Preserves form input state in sessionStorage so that no user entries are lost
 * if user navigates or refreshes.
 */
function initFormStatePersistence(formId, storageKey) {
  const form = document.getElementById(formId);
  if (!form) return;

  // Restore draft if present
  try {
    const saved = sessionStorage.getItem(storageKey);
    if (saved) {
      const data = JSON.parse(saved);
      for (const [key, value] of Object.entries(data)) {
        const field = form.elements[key];
        if (field && !field.value && value !== undefined && value !== null) {
          if (field.type === 'checkbox') {
            field.checked = Boolean(value);
          } else {
            field.value = value;
          }
          field.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
    }
  } catch (e) {
    console.debug('Failed to restore form state:', e);
  }

  // Check URL query parameters for auto-selection (e.g. ?customer_id=2 or ?company_id=1)
  const urlParams = new URLSearchParams(window.location.search);
  urlParams.forEach((val, key) => {
    const field = form.elements[key] || form.elements[key.replace('_id', '')];
    if (field) {
      field.value = val;
      field.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });

  // Save changes to sessionStorage
  const saveState = () => {
    const data = {};
    const elements = form.elements;
    for (let i = 0; i < elements.length; i++) {
      const el = elements[i];
      if (!el.name || el.name === 'csrfmiddlewaretoken' || el.type === 'password' || el.type === 'submit') continue;
      data[el.name] = el.type === 'checkbox' ? el.checked : el.value;
    }
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(data));
    } catch (e) {}
  };

  form.addEventListener('input', saveState);
  form.addEventListener('change', saveState);

  // Clear draft upon successful submit
  form.addEventListener('submit', () => {
    try {
      sessionStorage.removeItem(storageKey);
    } catch (e) {}
  });
}
