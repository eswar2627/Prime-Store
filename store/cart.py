from decimal import Decimal
from django.conf import settings
from store.models import Product

class Cart:
    SESSION_KEY = "cart"
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(self.SESSION_KEY)
        if cart is None:
            cart = self.session[self.SESSION_KEY] = {}
        self.cart = cart
    def add(self, product, quantity=1, override_quantity=False):
        pid = str(product.id)
        if pid not in self.cart:
            self.cart[pid] = {
                "quantity": 0,
                "price": str(product.price)  # store as string to save session safely
            }
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            quantity = 1
        if quantity < 0:
            quantity = 0
        if override_quantity:
            self.cart[pid]["quantity"] = quantity
        else:
            self.cart[pid]["quantity"] += quantity
        if self.cart[pid]["quantity"] <= 0:
            del self.cart[pid]
        else:
            self.save()
    def save(self):
        self.session[self.SESSION_KEY] = self.cart
        self.session.modified = True
    def remove(self, product):
        pid = str(product.id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()
    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            pid = str(product.id)
            item = self.cart[pid].copy()
            item["product"] = product
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["quantity"]
            yield item
    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())
    def get_total_price(self):
        return sum(
            Decimal(item["price"]) * item["quantity"]
            for item in self.cart.values()
        )
    def clear(self):
        self.cart = {}
        self.session[self.SESSION_KEY] = {}
        self.save()