from django.shortcuts import render, get_object_or_404
from .models import Category, Product
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem
import stripe
from django.conf import settings
from django.http import HttpResponse

from django.contrib.auth.models import User


def create_admin(request):
    if request.method == "GET":
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
            return HttpResponse("Admin created.")
        return HttpResponse("Admin already exists.")
    return HttpResponse("Invalid request method.", status=405)


#from django.core.management import call_command

#def load_fixtures(request):
   # try:
     #   call_command('loaddata', 'categories.json')
      #  call_command('loaddata', 'products.json')
     #   return HttpResponse("Fixtures loaded successfully.")
   # except Exception as e:
    #    return HttpResponse(f"Error loading fixtures: {e}")


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
def product_detail(request, id ,slug):
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

    return redirect('view_cart')



stripe.api_key = settings.STRIPE_SECRET_KEY
@login_required
def cart_detail(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        item_total = product.price * quantity
        total += item_total
        items.append({
            'product': product,
            'quantity': quantity,
            'total': item_total
        })

    context = {
        'cart_items': items,
        'cart_total': total,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
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
    return redirect('view_cart')

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
    return redirect('view_cart')
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

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cart/'),
        )
        return redirect(checkout_session.url)
    except Exception as e:
        return render(request, 'core/product/error.html', {'error': str(e)})

def payment_success(request):
    # Clear the cart
    request.session['cart'] = {}
    return render(request, 'core/product/success.html')





