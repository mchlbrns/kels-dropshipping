from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('shop/', views.store_catalog, name='store_catalog'),
    path('p/<slug:slug>/', views.product_detail, name='product_detail'),
    path('order/payment-success/', views.payment_success, name='payment_success'),
    path('order/paymongo-webhook/', views.paymongo_webhook, name='paymongo_webhook'),
    path('p/<slug:slug>/stock/', views.product_stock_api, name='product_stock_api'),
]
