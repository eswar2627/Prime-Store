from django.urls import path
from . import views

app_name = 'orders'
urlpatterns = [
    path('history/', views.order_history, name='order_history'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('create/', views.order_create, name='order_create'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('<int:order_id>/invoice/', views.invoice_pdf, name='invoice'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]