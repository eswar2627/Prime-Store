from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from orders.models import Order, OrderItem
from store.models import Product
from django.db.models import Sum, F, FloatField, Count
from datetime import timedelta
from django.utils import timezone
from django.db.models.functions import TruncMonth
import csv
from django.http import HttpResponse
import openpyxl

@staff_member_required
def dashboard(request):
    today = timezone.now().date()
    total_orders = Order.objects.count()
    total_revenue = OrderItem.objects.aggregate(
        total=Sum(F("price") * F("quantity"), output_field=FloatField())
    )["total"] or 0
    orders_today = Order.objects.filter(created__date=today).count()
    revenue_today = OrderItem.objects.filter(
        order__paid=True,
        order__created__date=today
    ).aggregate(
        total=Sum(F("price") * F("quantity"), output_field=FloatField())
    )["total"] or 0
    customer_orders = (
        Order.objects.values("email")
        .annotate(order_count=Count("id"))
    )
    new_customers = sum(1 for c in customer_orders if c["order_count"] == 1)
    returning_customers = sum(1 for c in customer_orders if c["order_count"] > 1)
    monthly_new_customers = (
        Order.objects.annotate(month=TruncMonth("created"))
        .values("month")
        .annotate(new_count=Count("email", distinct=True))
        .order_by("month")
    )
    customer_month_labels = [item["month"].strftime("%b %Y") for item in monthly_new_customers]
    customer_month_data = [item["new_count"] for item in monthly_new_customers]
    top_customers = (
        Order.objects.values("email")
        .annotate(order_count=Count("id"))
        .order_by("-order_count")[:5]
    )
    top_products = (
        OrderItem.objects.values("product__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:5]
    )
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    date_labels = [d.strftime("%b %d") for d in last_7_days]
    sales_data = [
        OrderItem.objects.filter(order__paid=True, order__created__date=day)
        .aggregate(total=Sum(F("price") * F("quantity"), output_field=FloatField()))
        ["total"] or 0
        for day in last_7_days
    ]
    paid_orders = Order.objects.filter(paid=True).count()
    unpaid_orders = Order.objects.filter(paid=False).count()
    monthly_sales = (
        OrderItem.objects.filter(order__paid=True)
        .annotate(month=TruncMonth("order__created"))
        .values("month")
        .annotate(total=Sum(F("price") * F("quantity")))
        .order_by("month")
    )
    months_labels = [item["month"].strftime("%b %Y") for item in monthly_sales]
    months_data = [float(item["total"]) for item in monthly_sales]
    product_revenue = (
        OrderItem.objects.annotate(total_amount=F("price") * F("quantity"))
        .values("product__name")
        .annotate(total_revenue=Sum("total_amount"))
        .order_by("-total_revenue")[:10]
    )
    revenue_labels = [item["product__name"] for item in product_revenue]
    revenue_data = [float(item["total_revenue"]) for item in product_revenue]
    recent_orders = Order.objects.order_by("-created")[:10]
    low_stock_products = Product.objects.filter(stock__lte=5).order_by("stock")
    context = {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "orders_today": orders_today,
        "revenue_today": revenue_today,
        "top_products": top_products,
        "sales_data": sales_data,
        "date_labels": date_labels,
        "paid_orders": paid_orders,
        "unpaid_orders": unpaid_orders,
        "months_labels": months_labels,
        "months_data": months_data,
        "revenue_labels": revenue_labels,
        "revenue_data": revenue_data,
        "recent_orders": recent_orders,
        "low_stock_products": low_stock_products,
        "new_customers": new_customers,
        "returning_customers": returning_customers,
        "customer_month_labels": customer_month_labels,
        "customer_month_data": customer_month_data,
        "top_customers": top_customers,
    }
    return render(request, "dashboard/dashboard.html", context)
@staff_member_required
def export_orders_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Customer Email", "Total Cost", "Paid", "Created"])
    for order in Order.objects.all():
        total_cost = sum(item.price * item.quantity for item in order.items.all())
        writer.writerow([order.id, order.email, float(total_cost), order.paid, order.created])
    return response
@staff_member_required
def export_orderitems_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="order_items.csv"'
    writer = csv.writer(response)
    writer.writerow(["Order ID", "Product", "Price", "Quantity", "Subtotal"])
    for item in OrderItem.objects.all():
        writer.writerow([
            item.order.id,
            item.product.name,
            float(item.price),
            item.quantity,
            float(item.price * item.quantity)
        ])
    return response
@staff_member_required
def export_orders_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders"
    ws.append(["ID", "Customer Email", "Total Cost", "Paid", "Created"])
    for order in Order.objects.all():
        total_cost = sum(item.price * item.quantity for item in order.items.all())
        ws.append([
            order.id,
            order.email,
            float(total_cost),
            order.paid,
            order.created.strftime("%Y-%m-%d %H:%M")
        ])
    response = HttpResponse(
        content=openpyxl.writer.excel.save_virtual_workbook(wb),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="orders.xlsx"'
    return response
@staff_member_required
def export_orderitems_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Order Items"
    ws.append(["Order ID", "Product", "Price", "Quantity", "Subtotal"])
    for item in OrderItem.objects.all():
        ws.append([
            item.order.id,
            item.product.name,
            float(item.price),
            item.quantity,
            float(item.price * item.quantity)
        ])
    response = HttpResponse(
        content=openpyxl.writer.excel.save_virtual_workbook(wb),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="order_items.xlsx"'
    return response