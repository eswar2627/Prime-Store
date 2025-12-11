from django.urls import path
from . import views
from .views import (
    SaveDeviceTokenAPI,
    SendNotificationToUserAPI,
    SendBroadcastNotificationAPI
)
urlpatterns = [
    # Product APIs
    path('products/', views.ProductListAPI.as_view()),
    path('products/<int:pk>/', views.ProductDetailAPI.as_view()),
    # Categories
    path('categories/', views.CategoryListAPI.as_view()),
    path('orders/', views.OrderCreateAPI.as_view()),
    path('orders/history/', views.OrderHistoryAPI.as_view()),
    path('recommendations/popular/', views.PopularProductsAPI.as_view(), name='popular_products'),
    path('recommendations/product/<int:product_id>/similar/', views.SimilarProductsAPI.as_view(), name='similar_products'),
    path('recommendations/for-you/', views.ForYouRecommendationsAPI.as_view(), name='for_you_recommendations'),
    path('auth/register/', views.RegisterAPI.as_view()),
    path('cart/', views.CartListAPI.as_view(), name='cart_list'),
    path('cart/add/', views.CartAddAPI.as_view(), name='cart_add'),
    path('cart/item/<int:pk>/', views.CartItemUpdateAPI.as_view(), name='cart_item_update'),
    path('cart/item/<int:pk>/delete/', views.CartItemDeleteAPI.as_view(), name='cart_item_delete'),
    path('cart/clear/', views.CartClearAPI.as_view(), name='cart_clear'),
    path('wishlist/', views.WishlistListAPI.as_view(), name='wishlist_list'),
    path('wishlist/add/', views.WishlistAddAPI.as_view(), name='wishlist_add'),
    path('wishlist/item/<int:pk>/delete/', views.WishlistDeleteAPI.as_view(), name='wishlist_delete'),
    path('wishlist/check/<int:product_id>/', views.WishlistCheckAPI.as_view(), name='wishlist_check'),
    path("payment/stripe/create/", views.StripeCreatePaymentIntentAPI.as_view()),
    path("payment/stripe/webhook/", views.stripe_webhook),
    path("reviews/product/<int:product_id>/", views.ProductReviewListAPI.as_view()),
    path("reviews/product/<int:product_id>/add/", views.AddReviewAPI.as_view()),
    path("reviews/summary/<int:product_id>/", views.ProductRatingSummaryAPI.as_view()),
    path("reviews/check/<int:product_id>/", views.CheckUserReviewAPI.as_view()),
    path("reviews/update/<int:review_id>/", views.UpdateReviewAPI.as_view()),
    path("reviews/delete/<int:review_id>/", views.DeleteReviewAPI.as_view()),
    path("coupon/apply/", views.ApplyCouponAPI.as_view(), name="coupon_apply"),
    path("coupon/remove/", views.RemoveCouponAPI.as_view(), name="coupon_remove"),
    path("coupon/list/", views.CouponListAPI.as_view(), name="coupon_list"),
    path("notifications/token/save/", SaveDeviceTokenAPI.as_view()),
    path("notifications/send/", SendNotificationToUserAPI.as_view()),
    path("notifications/send-all/", SendBroadcastNotificationAPI.as_view()),
]