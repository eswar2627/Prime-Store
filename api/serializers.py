from rest_framework import serializers
from orders.models import Order, OrderItem
from django.contrib.auth.models import User
from store.models import Product, Category, CartItem
from store.models import Review
from store.models import Wishlist
from store.models import Coupon

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'
class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # show username
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created', 'updated']
        read_only_fields = ['id', 'user', 'created', 'updated']
class ProductMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image']
class WishlistSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(available=True),
        source='product',
        write_only=True
    )
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id', 'created']
        read_only_fields = ['id', 'product', 'created']
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(available=True),
        source='product',
        write_only=True
    )
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price']
        read_only_fields = ['id', 'product', 'total_price']
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'price', 'image', 'stock', 'category'
        ]
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'price', 'quantity']
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        fields = [
            'id', 'email', 'address', 'city',
            'postal_code', 'created', 'paid', 'items'
        ]
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user