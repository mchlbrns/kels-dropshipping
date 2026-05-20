from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('p/<slug:slug>/', views.product_detail, name='product_detail'),
]
