from decimal import Decimal
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Avg
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from store.models import Product, Category, CartItem, Wishlist, Coupon, Review
from orders.models import Order, OrderItem
from accounts.models import DeviceToken
from .serializers import (
    ProductSerializer,
    CategorySerializer,
    CartItemSerializer,
    WishlistSerializer,
    RegisterSerializer,
    OrderSerializer,
    ReviewSerializer,
    CouponSerializer,
    ProductMiniSerializer,
)
from notifications.utils import send_fcm_notification

stripe.api_key = settings.STRIPE_SECRET_KEY
class ProductListAPI(generics.ListAPIView):
    queryset = Product.objects.filter(available=True)
    serializer_class = ProductSerializer
class ProductDetailAPI(generics.RetrieveAPIView):
    queryset = Product.objects.filter(available=True)
    serializer_class = ProductSerializer
class CategoryListAPI(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
class CartListAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        items = CartItem.objects.filter(user=request.user).select_related("product")
        serializer = CartItemSerializer(items, many=True)
        total = sum(float(i["total_price"]) for i in serializer.data)
        return Response({"items": serializer.data, "total": total})
class CartAddAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        data = request.data.copy()
        data.setdefault("quantity", 1)
        serializer = CartItemSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]
        item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity += quantity
            item.save()
        return Response(
            {
                "message": "Item added to cart",
                "cart_item_id": item.id,
                "quantity": item.quantity,
            },
            status=status.HTTP_200_OK,
        )
class CartItemUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, pk):
        try:
            item = CartItem.objects.get(id=pk, user=request.user)
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        quantity = int(request.data.get("quantity", 0))
        if quantity <= 0:
            item.delete()
            return Response(
                {"message": "Item removed from cart"},
                status=status.HTTP_200_OK,
            )
        item.quantity = quantity
        item.save()
        return Response(
            {"message": "Quantity updated", "quantity": item.quantity},
            status=status.HTTP_200_OK,
        )
class CartItemDeleteAPI(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, pk):
        try:
            item = CartItem.objects.get(id=pk, user=request.user)
        except CartItem.DoesNotExist:
            return Response(
                {"detail": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        item.delete()
        return Response({"message": "Item removed"}, status=status.HTTP_200_OK)
class CartClearAPI(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        CartItem.objects.filter(user=request.user).delete()
        return Response({"message": "Cart cleared"}, status=status.HTTP_200_OK)
class WishlistListAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        items = Wishlist.objects.filter(user=request.user).select_related("product")
        serializer = WishlistSerializer(items, many=True)
        return Response(serializer.data)
class WishlistAddAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = WishlistSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        product = serializer.validated_data["product"]
        item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product,
        )
        if not created:
            return Response({"message": "Already in wishlist"}, status=status.HTTP_200_OK)
        return Response({"message": "Item added to wishlist"}, status=status.HTTP_201_CREATED)
class WishlistDeleteAPI(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, pk):
        try:
            item = Wishlist.objects.get(id=pk, user=request.user)
        except Wishlist.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response({"message": "Removed from wishlist"}, status=status.HTTP_200_OK)
class WishlistCheckAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, product_id):
        exists = Wishlist.objects.filter(
            user=request.user,
            product_id=product_id,
        ).exists()
        return Response({"wishlisted": exists})
class RegisterAPI(generics.CreateAPIView):
    """User registration API."""
    serializer_class = RegisterSerializer
class OrderCreateAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, **kwargs):
        items_data = request.data.get("items")
        if not items_data:
            cart_items = CartItem.objects.filter(user=request.user).select_related("product")
            if not cart_items.exists():
                return Response(
                    {"detail": "Cart is empty"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            cart_items = None  # use payload
        order = Order.objects.create(
            email=request.user.email,
            address=request.data.get("address"),
            city=request.data.get("city"),
            postal_code=request.data.get("postal_code"),
            paid=False,
        )
        if cart_items is not None:
            # from CartItem model
            for ci in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=ci.product,
                    price=ci.product.price,
                    quantity=ci.quantity,
                )
            cart_items.delete()
        else:
            for item in items_data:
                product = Product.objects.get(id=item["product_id"])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.price,
                    quantity=item["quantity"],
                )
        return Response({"order_id": order.id}, status=status.HTTP_200_OK)
class OrderHistoryAPI(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Order.objects.filter(email=self.request.user.email)
class AddReviewAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, product_id):
        rating = int(request.data.get("rating", 0))
        comment = request.data.get("comment", "")
        if rating < 1 or rating > 5:
            return Response({"detail": "Rating must be 1 to 5"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(id=product_id, available=True)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        if Review.objects.filter(user=request.user, product=product).exists():
            return Response({"detail": "You already reviewed this product"}, status=status.HTTP_400_BAD_REQUEST)
        review = Review.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            comment=comment,
        )
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
class UpdateReviewAPI(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id, user=request.user)
        except Review.DoesNotExist:
            return Response({"detail": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
        if "rating" in request.data:
            rating = int(request.data["rating"])
            if 1 <= rating <= 5:
                review.rating = rating
        if "comment" in request.data:
            review.comment = request.data["comment"]
        review.save()
        return Response(ReviewSerializer(review).data)
class DeleteReviewAPI(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id, user=request.user)
        except Review.DoesNotExist:
            return Response({"detail": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
        review.delete()
        return Response({"message": "Review deleted"}, status=status.HTTP_200_OK)
class ProductReviewListAPI(APIView):
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id, available=True)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        reviews = product.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
class ProductRatingSummaryAPI(APIView):
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id, available=True)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        summary = product.reviews.aggregate(
            avg_rating=Avg("rating"),
            total=Count("id"),
        )
        star_counts = {
            star: product.reviews.filter(rating=star).count()
            for star in [5, 4, 3, 2, 1]
        }
        return Response(
            {
                "average_rating": summary["avg_rating"] or 0,
                "total_reviews": summary["total"] or 0,
                "stars": star_counts,
            }
        )
class CheckUserReviewAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, product_id):
        exists = Review.objects.filter(
            user=request.user,
            product_id=product_id,
        ).exists()
        return Response({"reviewed": exists})
class PopularProductsAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request):
        top_items = (
            OrderItem.objects
            .values("product_id")
            .annotate(total_qty=Sum("quantity"))
            .order_by("-total_qty")[:10]
        )
        product_ids = [item["product_id"] for item in top_items]
        products = list(Product.objects.filter(id__in=product_ids, available=True))
        products_sorted = sorted(products, key=lambda p: product_ids.index(p.id))
        serializer = ProductMiniSerializer(products_sorted, many=True)
        return Response(serializer.data)
class SimilarProductsAPI(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id, available=True)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        similar = (
            Product.objects
            .filter(category=product.category, available=True)
            .exclude(id=product.id)[:10]
        )
        serializer = ProductMiniSerializer(similar, many=True)
        return Response(serializer.data)
class ForYouRecommendationsAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        ordered_product_ids = (
            OrderItem.objects
            .filter(order__email=user.email)
            .values_list("product_id", flat=True)
        )
        ordered_categories = (
            Product.objects
            .filter(id__in=ordered_product_ids)
            .values_list("category_id", flat=True)
        )
        wish_product_ids = (
            Wishlist.objects
            .filter(user=user)
            .values_list("product_id", flat=True)
        )
        wish_categories = (
            Product.objects
            .filter(id__in=wish_product_ids)
            .values_list("category_id", flat=True)
        )
        category_ids = set(list(ordered_categories) + list(wish_categories))
        if not category_ids:
            top_items = (
                OrderItem.objects
                .values("product_id")
                .annotate(total_qty=Sum("quantity"))
                .order_by("-total_qty")[:10]
            )
            product_ids = [item["product_id"] for item in top_items]
            products = Product.objects.filter(id__in=product_ids, available=True)
        else:
            exclude_ids = set(list(ordered_product_ids) + list(wish_product_ids))
            products = (
                Product.objects
                .filter(category_id__in=category_ids, available=True)
                .exclude(id__in=exclude_ids)[:20]
            )
        serializer = ProductMiniSerializer(products, many=True)
        return Response(serializer.data)
class ApplyCouponAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        code = request.data.get("code", "").strip().upper()
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({"detail": "Invalid coupon"}, status=status.HTTP_400_BAD_REQUEST)
        if not coupon.is_valid():
            return Response({"detail": "Coupon expired or inactive"}, status=status.HTTP_400_BAD_REQUEST)
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
        cart_total = sum(ci.total_price for ci in cart_items)
        if cart_total < coupon.min_order_amount:
            return Response(
                {"detail": f"Minimum order amount is ₹{coupon.min_order_amount}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if coupon.discount_type == "flat":
            discount = Decimal(coupon.amount)
        else:
            discount = (cart_total * coupon.amount) / Decimal(100)
        discount = min(discount, cart_total)
        payable = cart_total - discount
        return Response(
            {
                "code": coupon.code,
                "discount": float(discount),
                "total_before": float(cart_total),
                "total_after": float(payable),
            }
        )
class RemoveCouponAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        return Response({"message": "Coupon removed"})
class CouponListAPI(APIView):
    def get(self, request):
        coupons = Coupon.objects.filter(active=True, expiry_date__gte=timezone.now())
        serializer = CouponSerializer(coupons, many=True)
        return Response(serializer.data)
class StripeCreatePaymentIntentAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        order_id = request.data.get("order_id")
        try:
            order = Order.objects.get(id=order_id, paid=False)
        except Order.DoesNotExist:
            return Response({"detail": "Invalid order id"}, status=status.HTTP_404_NOT_FOUND)
        amount = int(order.get_total_cost() * 100)
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="inr",  # or "usd"
            metadata={"order_id": order.id},
        )
        return Response(
            {
                "client_secret": intent.client_secret,
                "public_key": settings.STRIPE_PUBLIC_KEY,
            }
        )
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except Exception:
        return HttpResponse(status=400)
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        order_id = intent["metadata"]["order_id"]
        try:
            order = Order.objects.get(id=order_id)
            order.paid = True
            order.save()
        except Order.DoesNotExist:
            pass
    return HttpResponse(status=200)
class SaveDeviceTokenAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        token = request.data.get("token")
        device_type = request.data.get("device_type", "android")
        if not token:
            return Response({"detail": "Token required"}, status=status.HTTP_400_BAD_REQUEST)
        DeviceToken.objects.update_or_create(
            user=request.user,
            token=token,
            defaults={"device_type": device_type},
        )
        return Response({"message": "Token saved"}, status=status.HTTP_200_OK)
class SendNotificationToUserAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user_id = request.data.get("user_id")
        title = request.data.get("title")
        body = request.data.get("body")
        if not user_id or not title or not body:
            return Response(
                {"detail": "user_id, title and body are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tokens = DeviceToken.objects.filter(user_id=user_id)
        if not tokens.exists():
            return Response(
                {"detail": "User has no device tokens"},
                status=status.HTTP_404_NOT_FOUND,
            )
        for t in tokens:
            send_fcm_notification(t.token, title, body)
        return Response({"message": "Notification sent"}, status=status.HTTP_200_OK)
class SendBroadcastNotificationAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        title = request.data.get("title")
        body = request.data.get("body")
        if not title or not body:
            return Response(
                {"detail": "title and body are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tokens = DeviceToken.objects.all()
        if not tokens.exists():
            return Response(
                {"detail": "No device tokens found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        for t in tokens:
            send_fcm_notification(t.token, title, body)
        return Response({"message": "Broadcast sent"}, status=status.HTTP_200_OK)