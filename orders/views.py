from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from store.cart import Cart
from accounts.models import Address
from .models import Order, OrderItem
from reportlab.pdfgen import canvas
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'accounts/order_history.html', {'orders': orders})
@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, "Your cart is empty.")
        return redirect('store:product_list')
    addresses = Address.objects.filter(user=request.user)
    if request.method == "POST":
        selected_address_id = request.POST.get("selected_address")
        payment_method = request.POST.get("payment_method", "ONLINE")  # default ONLINE
        if not selected_address_id:
            messages.error(request, "Please select a delivery address.")
            return redirect("orders:order_create")
        address = get_object_or_404(Address, id=selected_address_id, user=request.user)
        full_name_parts = address.full_name.split()
        first_name = full_name_parts[0] if full_name_parts else ""
        last_name = " ".join(full_name_parts[1:]) if len(full_name_parts) > 1 else ""
        order = Order.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            email=request.user.email,
            address=address.address,
            postal_code=address.postal_code,
            city=address.city,
            paid=False,
        )
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                price=item["price"],
                quantity=item["quantity"]
            )
        if payment_method == "COD":
            order.status = "PLACED"
            order.paid = False
            order.save()
            cart.clear()
            messages.success(request, "Order placed successfully with Cash on Delivery.")
            return redirect("orders:order_detail", order_id=order.id)
        line_items = [
            {
                "price_data": {
                    "currency": "inr",
                    "product_data": {"name": item["product"].name},
                    "unit_amount": int(item["price"] * 100),
                },
                "quantity": item["quantity"],
            }
            for item in cart
        ]
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=request.build_absolute_uri(
                reverse("orders:stripe_success")
            ) + f"?order_id={order.id}",
            cancel_url=request.build_absolute_uri(reverse("orders:stripe_cancel")),
        )
        return redirect(session.url, code=303)
    return render(request, "orders/order_create.html", {
        "cart": cart,
        "addresses": addresses,
    })
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/order_details.html", {"order": order})
@login_required
def stripe_success(request):
    order_id = request.GET.get("order_id")
    if not order_id:
        messages.error(request, "Missing order ID in payment callback.")
        return redirect("store:product_list")
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.paid = True
    order.status = "PLACED"
    order.save()
    cart = Cart(request)
    cart.clear()
    return render(request, "orders/stripe_success.html", {"order": order})
@login_required
def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=\"invoice_{order.id}.pdf\""'
    p = canvas.Canvas(response)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(200, 800, "PrimeStore Invoice")
    p.setFont("Helvetica", 12)
    p.drawString(50, 760, f"Order ID: {order.id}")
    p.drawString(50, 740, f"Tracking Number: {getattr(order, 'tracking_number', '')}")
    p.drawString(50, 720, f"Customer Email: {order.email}")
    p.drawString(50, 700, f"Order Date: {order.created.strftime('%d-%m-%Y %H:%M')}")
    p.drawString(50, 670, "Items:")
    y = 650
    for item in order.items.all():
        p.drawString(60, y, f"{item.product.name} x{item.quantity} — ₹{item.get_cost()}")
        y -= 20
        if y < 80:
            p.showPage()
            y = 800
    p.drawString(50, y - 20, f"Total: ₹{order.get_total_cost()}")
    p.showPage()
    p.save()
    return response
def stripe_cancel(request):
    return render(request, "orders/stripe_cancel.html")
@csrf_exempt
def stripe_webhook(request):
    return HttpResponse(status=200)