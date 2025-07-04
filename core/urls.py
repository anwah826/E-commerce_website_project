from django.urls import path
from . import views
from .views import remove_from_cart, update_cart_quantity
from django.contrib.auth import views as auth_views
from .views import load_fixtures, create_admin

urlpatterns = [
    path('', views.product_list, name='product_list'),  
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),  # keep only one
    path('accounts/login/', auth_views.LoginView.as_view(template_name='core/product/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('register/', views.register, name='register'),
    path('checkout/', views.checkout, name='checkout'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('success/', views.payment_success, name='payment_success'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('support/', views.support_view, name='support'),
    path('load-fixtures/', load_fixtures, name='load_fixtures'),
    path('create-admin/', create_admin, name='create_admin'),
]

