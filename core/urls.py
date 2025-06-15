from django.urls import path
from . import views
from .views import remove_from_cart, update_cart_quantity
from django.contrib.auth import views as auth_views
#from .views import load_fixtures
#urlpatterns = [
   # path('', views.product_list, name='product_list'),
    
  #  path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
   # path('cart/', views.cart_detail, name='cart_detail'),
   
   # path('remove-from-cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
   # path('update-cart/<int:item_id>/<str:action>/', update_cart_quantity, name='update_cart_quantity'),
   # path('cart/', views.view_cart, name='view_cart'),
#]

urlpatterns = [
    path('', views.product_list, name='product_list'),  
    path('accounts/login/', auth_views.LoginView.as_view(template_name='core/product/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'), 
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('register/', views.register, name='register'),

    path('checkout/', views.checkout, name='checkout'),
    path('success/', views.payment_success, name='payment_success'),
    
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    #path('load-fixtures/', load_fixtures, name='load_fixtures'),
]
