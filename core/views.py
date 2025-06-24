from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Cart, CartItem
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.core.management import call_command
from django.contrib.auth.models import User
import stripe
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.urls import reverse

def support_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        full_message = f"From: {email}\n\n{message}"

        send_mail(
            subject,
            full_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.SUPPORT_EMAIL],
        )

        return render(request, 'core/product/support.html', {'success': True})

    return render(request, 'core/product/support.html')

@login_required
def user_dashboard(request):
    cart_items = CartItem.objects.filter(session_key=get_cart_session_key(request))
    return render(request, 'core/product/dashboard.html', {
        'user': request.user,
        'cart_items': cart_items,
    })

def create_admin(request):
    if User.objects.filter(username='admin').exists():
        return HttpResponse("Admin user already exists.")
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
    return HttpResponse("Admin user created.")


def check_admin(request):
    try:
        user = User.objects.get(username='admin')
        info = f"User: {user.username}, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}"
    except User.DoesNotExist:
        info = "Admin user does not exist."
    return HttpResponse(info)


def load_fixtures(request):
    try:
        call_command('loaddata', 'categories.json')
        call_command('loaddata', 'products.json')
        return HttpResponse("Fixtures loaded successfully.")
    except Exception as e:
        return HttpResponse(f"Error loading fixtures: {e}")


def get_cart_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


@login_required
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    paginator = Paginator(products, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/product/list.html', {
        'category': category,
        'categories': categories,
        'products': page_obj,
        'query': query,
    })


@login_required
def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    return render(request, 'core/product/detail.html', {'product': product})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'core/product/register.html', {'form': form})


def get_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart




@login_required
def add_to_cart(request, product_id):
    session_key = get_cart_session_key(request)
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(
        product=product,
        session_key=session_key,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"✅ {product.name} was added to your cart.")
    return redirect(reverse('product_detail', args=[product.id, product.slug]))



stripe.api_key = settings.STRIPE_SECRET_KEY
@login_required
def cart_detail(request):
    session_key = get_cart_session_key(request)  # get user's session key
    cart_items = CartItem.objects.filter(session_key=session_key)
    cart_total = sum(item.quantity * item.product.price for item in cart_items)
    stripe_amount_cents = int(cart_total * 100)

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'stripe_amount_cents': stripe_amount_cents,
    }
    return render(request, 'core/product/cart.html', context)


def view_cart(request):
    session_key = get_cart_session_key(request)
    cart_items = CartItem.objects.filter(session_key=session_key)
    cart_total = sum(item.total_price() for item in cart_items)
    return render(request, 'core/product/cart.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
    })


def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect('cart_detail')


def update_cart_quantity(request, item_id, action):
    item = get_object_or_404(CartItem, id=item_id)
    if action == 'increase':
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    return redirect('cart_detail')  


def checkout(request):
    cart = request.session.get('cart', {})
    line_items = []

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product.name,
                },
                'unit_amount': int(product.price * 100),
            },
            'quantity': quantity,
        })

    # ✅ Production domain (Render)
    YOUR_DOMAIN = 'https://e-commerce-website-project-xqdz.onrender.com'

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success/',
            cancel_url=YOUR_DOMAIN + '/cart/',
        )
        return redirect(checkout_session.url)
    except Exception as e:
        return render(request, 'core/product/error.html', {'error': str(e)})


def payment_success(request):
    # Clear the cart
    request.session['cart'] = {}
    return render(request, 'core/product/success.html')


