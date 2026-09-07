/**
 * CodeAlpha E-Commerce Store - Main JavaScript Engine
 * Handles dynamic AJAX cart operations, CSRF headers, and UI feedback without full page reloads.
 */

document.addEventListener('DOMContentLoaded', () => {
  initAddToCartHandlers();
  initCartQuantityHandlers();
  initCartRemoveHandlers();
});

/**
 * Helper function to retrieve Django CSRF Cookie Token.
 */
function getCsrfToken() {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, 10) === 'csrftoken=') {
        cookieValue = decodeURIComponent(cookie.substring(10));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Displays modern popup toast notifications.
 */
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
    </svg>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/**
 * Updates navigation cart badge with smooth scale bump animation.
 */
function updateCartBadge(count) {
  const badge = document.getElementById('cart-badge');
  if (badge) {
    badge.textContent = count;
    badge.classList.add('bump');
    setTimeout(() => badge.classList.remove('bump'), 300);
  }
}

/**
 * Attaches event listeners for AJAX Add-to-Cart buttons.
 */
function initAddToCartHandlers() {
  document.querySelectorAll('.ajax-add-to-cart').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const url = form.action;
      const formData = new FormData(form);
      const submitBtn = form.querySelector('button[type="submit"]');

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.7';
      }

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          },
          body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
          updateCartBadge(data.cart_total_count);
          showToast(data.message || 'Added to cart!');
        } else {
          showToast(data.message || 'Error adding to cart.', 'error');
        }
      } catch (err) {
        console.error('Add to cart AJAX error:', err);
        showToast('Failed to add product to cart.', 'error');
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.style.opacity = '1';
        }
      }
    });
  });
}

/**
 * Dynamic quantity adjustment (+ / - and input change) on the Cart Page.
 */
function initCartQuantityHandlers() {
  document.querySelectorAll('.cart-qty-change').forEach(button => {
    button.addEventListener('click', async (e) => {
      e.preventDefault();
      const itemId = button.dataset.itemId;
      const action = button.dataset.action; // 'increment' or 'decrement'
      const qtyInput = document.getElementById(`qty-input-${itemId}`);
      if (!qtyInput) return;

      let currentQty = parseInt(qtyInput.value) || 1;
      let newQty = action === 'increment' ? currentQty + 1 : currentQty - 1;

      if (newQty < 1) newQty = 0; // Triggers removal if 0

      await updateCartItemQuantity(itemId, newQty);
    });
  });

  document.querySelectorAll('.cart-qty-input').forEach(input => {
    input.addEventListener('change', async (e) => {
      const itemId = input.dataset.itemId;
      let newQty = parseInt(input.value) || 1;
      if (newQty < 1) newQty = 1;
      await updateCartItemQuantity(itemId, newQty);
    });
  });
}

/**
 * Sends AJAX request to update quantity and recalculates totals dynamically.
 */
async function updateCartItemQuantity(itemId, quantity) {
  const url = `/cart/update/${itemId}/`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({ quantity: quantity })
    });

    const data = await response.json();

    if (data.success) {
      const row = document.getElementById(`cart-row-${itemId}`);
      
      if (data.removed) {
        if (row) row.remove();
        showToast('Item removed from cart');
      } else {
        const subtotalEl = document.getElementById(`subtotal-${itemId}`);
        const qtyInput = document.getElementById(`qty-input-${itemId}`);
        if (subtotalEl) subtotalEl.textContent = `$${data.item_subtotal.toFixed(2)}`;
        if (qtyInput) qtyInput.value = quantity;
      }

      updateCartSummary(data);
      updateCartBadge(data.cart_total_count);

      // Check if cart is now empty
      const remainingRows = document.querySelectorAll('.cart-row');
      if (remainingRows.length === 0) {
        location.reload();
      }
    }
  } catch (err) {
    console.error('Cart update error:', err);
    showToast('Could not update cart quantity.', 'error');
  }
}

/**
 * Cart Item Removal Handler via AJAX.
 */
function initCartRemoveHandlers() {
  document.querySelectorAll('.cart-remove-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const itemId = btn.dataset.itemId;
      const url = `/cart/remove/${itemId}/`;

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        const data = await response.json();

        if (data.success) {
          const row = document.getElementById(`cart-row-${itemId}`);
          if (row) row.remove();
          
          updateCartSummary(data);
          updateCartBadge(data.cart_total_count);
          showToast(data.message || 'Item removed from cart.');

          const remainingRows = document.querySelectorAll('.cart-row');
          if (remainingRows.length === 0) {
            location.reload();
          }
        }
      } catch (err) {
        console.error('Remove cart item error:', err);
        showToast('Failed to remove item.', 'error');
      }
    });
  });
}

/**
 * Updates Summary totals on the Cart Page UI.
 */
function updateCartSummary(data) {
  const subtotalEl = document.getElementById('summary-subtotal');
  const shippingEl = document.getElementById('summary-shipping');
  const taxEl = document.getElementById('summary-tax');
  const grandTotalEl = document.getElementById('summary-grand-total');

  if (subtotalEl) subtotalEl.textContent = `$${data.cart_subtotal.toFixed(2)}`;
  if (shippingEl) shippingEl.textContent = data.shipping === 0 ? 'FREE' : `$${data.shipping.toFixed(2)}`;
  if (taxEl) taxEl.textContent = `$${data.tax.toFixed(2)}`;
  if (grandTotalEl) grandTotalEl.textContent = `$${data.grand_total.toFixed(2)}`;
}
