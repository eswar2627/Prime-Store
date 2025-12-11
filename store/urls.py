from django.urls import path
from . import views
from .views import stripe_checkout, payment_success, payment_cancel

app_name = 'store'
urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('product/quick/<int:pk>/', views.product_quick_view, name='product_quick_view'),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
    path('filters/', views.product_filters, name='product_filters'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/summary/', views.cart_summary, name='cart_summary'),
    path('wishlist/', views.wishlist_list, name='wishlist_list'),
    path('wishlist/add/<int:product_id>/', views.wishlist_add, name='wishlist_add'),
    path('wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),
    path('wishlist/toggle/ajax/', views.ajax_wishlist_toggle, name='ajax_wishlist_toggle'),
    path('product/<slug:slug>/review/add/', views.add_review, name='add_review'),
    path('product/<slug:slug>/review/edit/', views.edit_review, name='edit_review'),
    path('product/<slug:slug>/review/delete/', views.delete_review, name='delete_review'),
    path("pay/", stripe_checkout, name="stripe_checkout"),
    path("payment/success/", payment_success, name="payment_success"),
    path("payment/cancel/", payment_cancel, name="payment_cancel"),
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),
]