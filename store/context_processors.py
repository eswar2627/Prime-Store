from store.cart import Cart

def cart_count(request):
    try:
        cart = Cart(request)
        return {"cart_count": len(cart)}
    except:
        return {"cart_count": 0}