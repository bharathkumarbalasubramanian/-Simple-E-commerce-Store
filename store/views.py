import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import Product, Category, Cart, CartItem, Order, OrderItem
from .context_processors import get_cart_for_request

# ==========================================
# STOREFRONT & CATALOG VIEWS
# ==========================================

def product_list(request):
    """
    Renders the main storefront with search and category filtering.
    """
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()

    query = request.GET.get('q', '').strip()
    selected_category_slug = request.GET.get('category', '').strip()

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if selected_category_slug:
        products = products.filter(category__slug=selected_category_slug)

    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': selected_category_slug,
    }
    return render(request, 'store/index.html', context)


def product_detail(request, slug):
    """
    Displays full details for a single product.
    """
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related_products = Product.objects.filter(
        category=product.category, is_available=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)


# ==========================================
# SHOPPING CART VIEWS (SESSION & DB SYNC)
# ==========================================

def cart_detail(request):
    """
    Renders the shopping cart page with items, tax, and order totals.
    Cart session logic: Retrieve cart via get_cart_for_request helper which binds
    the browser session_key or authenticated user instance.
    """
    cart = get_cart_for_request(request)
    cart_items = cart.items.select_related('product').all() if cart else []
    
    subtotal = cart.get_total_price() if cart else 0
    shipping = 10.00 if subtotal > 0 and subtotal < 100 else 0.00  # Free shipping over $100
    tax = round(float(subtotal) * 0.08, 2)  # 8% estimated tax
    grand_total = round(float(subtotal) + shipping + tax, 2)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)


@require_POST
def cart_add(request, product_id):
    """
    Adds a product to the user/session cart.
    Supports both traditional Form submissions and dynamic AJAX fetch requests.
    """
    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = get_cart_for_request(request)

    # Determine quantity from request (POST payload or JSON body)
    quantity = 1
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            quantity = int(body.get('quantity', 1))
        except (ValueError, json.JSONDecodeError):
            quantity = 1
    else:
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1

    if quantity < 1:
        quantity = 1

    # Check stock limitation
    if quantity > product.stock:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'message': f'Only {product.stock} units available in stock.'}, status=400)
        messages.error(request, f'Only {product.stock} units available in stock.')
        return redirect('product_detail', slug=product.slug)

    # Add or update CartItem
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            new_quantity = product.stock
        cart_item.quantity = new_quantity
        cart_item.save()

    # Dynamic AJAX Response
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json'
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': f'"{product.name}" added to cart!',
            'cart_total_count': cart.get_total_quantity(),
            'cart_total_price': float(cart.get_total_price()),
        })

    messages.success(request, f'"{product.name}" added to cart successfully!')
    return redirect('cart_detail')


@require_POST
def cart_update(request, item_id):
    """
    Updates the quantity of a specific cart item via AJAX or POST form.
    """
    cart = get_cart_for_request(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

    quantity = 1
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            quantity = int(body.get('quantity', 1))
        except (ValueError, json.JSONDecodeError):
            quantity = 1
    else:
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json'

    if quantity <= 0:
        cart_item.delete()
        removed = True
    else:
        if quantity > cart_item.product.stock:
            quantity = cart_item.product.stock
        cart_item.quantity = quantity
        cart_item.save()
        removed = False

    subtotal = cart.get_total_price()
    shipping = 10.00 if subtotal > 0 and subtotal < 100 else 0.00
    tax = round(float(subtotal) * 0.08, 2)
    grand_total = round(float(subtotal) + shipping + tax, 2)

    if is_ajax:
        return JsonResponse({
            'success': True,
            'removed': removed,
            'item_subtotal': float(cart_item.subtotal) if not removed else 0,
            'cart_total_count': cart.get_total_quantity(),
            'cart_subtotal': float(subtotal),
            'shipping': float(shipping),
            'tax': tax,
            'grand_total': grand_total,
        })

    return redirect('cart_detail')


@require_POST
def cart_remove(request, item_id):
    """
    Removes an item completely from the cart.
    """
    cart = get_cart_for_request(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product_name = cart_item.product.name
    cart_item.delete()

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json'
    
    subtotal = cart.get_total_price()
    shipping = 10.00 if subtotal > 0 and subtotal < 100 else 0.00
    tax = round(float(subtotal) * 0.08, 2)
    grand_total = round(float(subtotal) + shipping + tax, 2)

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': f'"{product_name}" removed from cart.',
            'cart_total_count': cart.get_total_quantity(),
            'cart_subtotal': float(subtotal),
            'shipping': float(shipping),
            'tax': tax,
            'grand_total': grand_total,
        })

    messages.info(request, f'"{product_name}" removed from your cart.')
    return redirect('cart_detail')


# ==========================================
# CHECKOUT & ORDER PROCESSING VIEWS
# ==========================================

def checkout(request):
    """
    Handles checkout form display and order processing.
    Converts active CartItems into an immutable Order & OrderItem record set.
    """
    cart = get_cart_for_request(request)
    cart_items = cart.items.select_related('product').all() if cart else []

    if not cart_items:
        messages.warning(request, 'Your cart is empty! Add products before checking out.')
        return redirect('product_list')

    subtotal = cart.get_total_price()
    shipping = 10.00 if subtotal > 0 and subtotal < 100 else 0.00
    tax = round(float(subtotal) * 0.08, 2)
    grand_total = round(float(subtotal) + shipping + tax, 2)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', 'USA').strip()

        if not all([full_name, email, address, city, postal_code]):
            messages.error(request, 'Please fill in all required shipping fields.')
            return render(request, 'store/checkout.html', {
                'cart': cart, 'cart_items': cart_items, 'subtotal': subtotal,
                'shipping': shipping, 'tax': tax, 'grand_total': grand_total
            })

        # Create Order record
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            address=address,
            city=city,
            postal_code=postal_code,
            country=country,
            total_price=grand_total,
            status='Completed'
        )

        # Move Cart Items into OrderItems and adjust Product stock
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity
            )
            # Deduct stock
            if item.product.stock >= item.quantity:
                item.product.stock -= item.quantity
                item.product.save()

        # Clear shopping cart after successful purchase
        cart.items.all().delete()

        messages.success(request, f'Thank you! Your order #{order.id} has been placed successfully.')
        return redirect('order_success', order_id=order.id)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)


def order_success(request, order_id):
    """
    Renders confirmation receipt for a placed order.
    """
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/order_success.html', {'order': order})


@login_required
def order_history(request):
    """
    Displays past orders for logged-in user.
    """
    orders = Order.objects.filter(user=request.user)
    return render(request, 'store/order_history.html', {'orders': orders})


# ==========================================
# USER AUTHENTICATION VIEWS
# ==========================================

def user_register(request):
    """
    User Registration View utilizing Django built-in UserCreationForm.
    """
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to CodeAlpha Store, {user.username}! Your account has been created.')
            return redirect('product_list')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = UserCreationForm()

    return render(request, 'store/register.html', {'form': form})


def user_login(request):
    """
    User Login View utilizing Django AuthenticationForm.
    """
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next') or 'product_list'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'store/login.html', {'form': form})


def user_logout(request):
    """
    User Logout View.
    """
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('product_list')
