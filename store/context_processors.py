from .models import Cart

def get_cart_for_request(request):
    """
    Helper function to retrieve or initialize a Cart instance.
    Uses request.session logic for guest users and request.user for logged-in users.
    Handles merging guest cart items into authenticated user cart upon login.
    """
    if not request.session.session_key:
        request.session.create()

    session_id = request.session.session_key

    if request.user.is_authenticated:
        # Check if user already has a cart
        user_cart, created = Cart.objects.get_or_create(user=request.user)

        # If guest session cart exists with items, merge items into user cart
        if session_id:
            guest_cart = Cart.objects.filter(session_id=session_id, user__isnull=True).first()
            if guest_cart:
                for item in guest_cart.items.all():
                    user_item, item_created = user_cart.items.get_or_create(
                        product=item.product,
                        defaults={'quantity': item.quantity}
                    )
                    if not item_created:
                        user_item.quantity += item.quantity
                        user_item.save()
                guest_cart.delete()

        return user_cart
    else:
        cart, created = Cart.objects.get_or_create(session_id=session_id, user__isnull=True)
        return cart


def cart_processor(request):
    """
    Django Context Processor to make cart data available across all templates.
    """
    cart = get_cart_for_request(request)
    total_count = cart.get_total_quantity() if cart else 0
    return {
        'cart': cart,
        'cart_total_count': total_count,
    }
