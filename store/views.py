from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.db.models import Q, Sum, F, FloatField, Avg, Min, Max
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.conf import settings
from django.contrib.auth.models import User
from .models import Product, Category, Wishlist, Review, ProductImage
from .forms import ReviewForm
from .cart import Cart

try:
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    _HAS_STRIPE = True
except Exception:
    stripe = None
    _HAS_STRIPE = False
def _parse_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
@ensure_csrf_cookie
@require_GET
def product_list(request, category_slug=None):
    qs = Product.objects.filter(available=True).select_related("category")
    categories = Category.objects.all()
    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        qs = qs.filter(category=category)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(brand__icontains=q)
        )
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    if min_price:
        try:
            qs = qs.filter(price__gte=Decimal(min_price))
        except Exception:
            pass
    if max_price:
        try:
            qs = qs.filter(price__lte=Decimal(max_price))
        except Exception:
            pass
    brand = request.GET.getlist("brand") or request.GET.get("brand")
    if isinstance(brand, str) and "," in brand:
        brand = [b.strip() for b in brand.split(",") if b.strip()]
    if brand:
        qs = qs.filter(brand__in=brand)
    rating_min = request.GET.get("rating_min")
    if rating_min:
        try:
            rating_min_val = float(rating_min)
            qs = qs.annotate(avg_rating=Avg("reviews__rating")).filter(avg_rating__gte=rating_min_val)
        except Exception:
            pass
    in_stock = request.GET.get("in_stock")
    if in_stock and in_stock.lower() in ("1", "true", "yes"):
        qs = qs.filter(stock__gt=0)
    sort = request.GET.get("sort", "")
    if sort == "low_price":
        qs = qs.order_by("price")
    elif sort == "high_price":
        qs = qs.order_by("-price")
    elif sort == "latest":
        qs = qs.order_by("-created")
    elif sort == "popular":
        if hasattr(Product, "sales_count"):
            qs = qs.order_by("-sales_count", "-created")
        else:
            qs = qs.order_by("-created")
    elif sort == "rating":
        qs = qs.annotate(avg_rating=Avg("reviews__rating")).order_by("-avg_rating", "-created")
    else:
        qs = qs.order_by("-created")
    page_number = _parse_int(request.GET.get("page"), 1) or 1
    page_size = _parse_int(request.GET.get("page_size"), 12) or 12
    paginator = Paginator(qs, page_size)
    products_page = paginator.get_page(page_number)
    price_agg = Product.objects.aggregate(min_price=Min("price"), max_price=Max("price"))
    context = {
        "category": category,
        "categories": categories,
        "products": products_page,
        "q": q,
        "min_price": min_price or "",
        "max_price": max_price or "",
        "sort": sort,
        "current_category_slug": category_slug,
        "price_min_global": price_agg.get("min_price") or 0,
        "price_max_global": price_agg.get("max_price") or 0,
        "page_number": page_number,
        "page_size": page_size,
        "total_items": paginator.count,
        "total_pages": paginator.num_pages,
    }
    return render(request, "store/product_list.html", context)
@require_GET
def search_suggest(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)
    limit = _parse_int(request.GET.get("limit"), 8) or 8
    category_slug = request.GET.get("category")
    qs = Product.objects.filter(available=True)
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    results = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(brand__icontains=q))[:limit]
    out = []
    for p in results:
        out.append({
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "thumbnail": p.image.url if getattr(p, "image", None) else "",
            "slug": p.slug,
            "url": p.get_absolute_url(),
        })
    return JsonResponse(out, safe=False)
@require_GET
def product_filters(request):
    category_slug = request.GET.get("category")
    qs = Product.objects.filter(available=True)
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    brands = list(qs.values_list("brand", flat=True).distinct().exclude(brand__isnull=True).exclude(brand__exact=""))
    categories = list(Category.objects.values("id", "name", "slug"))
    price_agg = qs.aggregate(min_price=Min("price"), max_price=Max("price"))
    return JsonResponse({
        "brands": brands,
        "categories": categories,
        "min_price": float(price_agg.get("min_price") or 0),
        "max_price": float(price_agg.get("max_price") or 0),
    })
@require_GET
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    user_review_exists = False
    if request.user.is_authenticated:
        user_review_exists = product.reviews.filter(user=request.user).exists()
    similar_products = Product.objects.filter(
        available=True,
        category=product.category
    ).exclude(id=product.id)[:8]
    recently_viewed_ids = request.session.get("recently_viewed", [])
    if product.id in recently_viewed_ids:
        recently_viewed_ids.remove(product.id)
    recently_viewed_ids.insert(0, product.id)
    request.session["recently_viewed"] = recently_viewed_ids[:10]
    recently_viewed_products = Product.objects.filter(id__in=recently_viewed_ids).exclude(id=product.id)
    recently_viewed_products = sorted(recently_viewed_products, key=lambda p: recently_viewed_ids.index(p.id)) if recently_viewed_products else []
    return render(request, "store/product_detail.html", {
        "product": product,
        "user_review_exists": user_review_exists,
        "similar_products": similar_products,
        "recently_viewed_products": recently_viewed_products,
    })
@require_GET
def product_quick_view(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    gallery_qs = getattr(product, "gallery", ProductImage.objects.none()).all()
    gallery_urls = [img.image.url for img in gallery_qs]
    variants = []
    if hasattr(product, "variants"):
        for v in getattr(product, "variants").all():
            variants.append({
                "id": v.id,
                "name": str(v),
                "price": str(getattr(v, "price", product.price)),
                "in_stock": getattr(v, "stock", 0) > 0,
            })
    return JsonResponse({
        "id": product.id,
        "name": product.name,
        "price": str(product.price),
        "image": product.image.url if getattr(product, "image", None) else "",
        "gallery": gallery_urls,
        "short_description": product.short_description if getattr(product, "short_description", None) else (product.description[:200] if product.description else ""),
        "description": product.description or "",
        "specs": {
            "brand": product.brand,
            "model_name": getattr(product, "model_name", ""),
            "screen_size": getattr(product, "screen_size", ""),
            "storage_capacity": getattr(product, "storage_capacity", ""),
        },
        "average_rating": product.reviews.aggregate(avg=Avg("rating"))["avg"] or 0,
        "stock": getattr(product, "stock", 0),
        "variants": variants,
        "url": request.build_absolute_uri(product.get_absolute_url()),
    })
@csrf_exempt
def stripe_checkout(request):
    if not _HAS_STRIPE:
        messages.error(request, "Payment gateway is not configured.")
        return redirect("store:cart_detail")
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, "Your cart is empty.")
        return redirect("store:cart_detail")
    line_items = []
    for item in cart:
        try:
            unit_amount = int(Decimal(item["price"]) * 100)
        except Exception:
            unit_amount = int(Decimal(0) * 100)
        line_items.append({
            "price_data": {
                "currency": "inr",
                "unit_amount": unit_amount,
                "product_data": {"name": item["product"].name},
            },
            "quantity": item["quantity"],
        })
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=request.build_absolute_uri(reverse("store:payment_success")),
        cancel_url=request.build_absolute_uri(reverse("store:payment_cancel")),
    )
    return redirect(session.url, code=303)
def payment_success(request):
    cart = Cart(request)
    cart.clear()
    return render(request, "store/payment_success.html")
def payment_cancel(request):
    return render(request, "store/payment_cancel.html")
def _is_ajax(request):
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"
    )
@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    try:
        qty = int(request.POST.get("quantity", 1))
    except:
        qty = 1
    override = str(request.POST.get("override", "false")).lower() == "true"
    cart.add(product=product, quantity=qty, override_quantity=override)
    if _is_ajax(request):
        return JsonResponse({
            "success": True,
            "product_id": product.id,
            "cart_count": len(cart),
            "message": f"{product.name} added to cart"
        })
    return redirect("store:cart_detail")
@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    request.session.modified = True
    if _is_ajax(request):
        return JsonResponse({
            "success": True,
            "cart_count": len(cart),
            "message": f"{product.name} removed"
        })
    return redirect("store:cart_detail")
@require_GET
def cart_detail(request):
    return render(request, "store/cart_detail.html", {"cart": Cart(request)})
@require_GET
def cart_summary(request):
    cart = Cart(request)
    items = []
    total = Decimal("0.00")
    for it in cart:
        items.append({
            "product_id": it["product"].id,
            "name": it["product"].name,
            "qty": it["quantity"],
            "unit_price": str(it["price"]),
            "subtotal": str(Decimal(it["price"]) * it["quantity"]),
            "thumbnail": getattr(it["product"], "image").url if getattr(it["product"], "image", None) else ""
        })
        total += (Decimal(it["price"]) * it["quantity"])
    return JsonResponse({
        "count": len(cart),
        "total": str(total),
        "items": items,
    })
@login_required
def wishlist_list(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product")
    return render(request, "store/wishlist_list.html", {"items": items})
@login_required
@require_POST
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "status": "added" if created else "exists",
            "product_id": product.id
        })
    if created:
        messages.success(request, f'"{product.name}" added to wishlist.')
    else:
        messages.info(request, f'"{product.name}" is already in your wishlist.')
    return redirect(product.get_absolute_url())
@login_required
@require_POST
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    deleted, _ = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).delete()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "status": "removed" if deleted else "not_found",
            "product_id": product.id
        })
    messages.info(request, f'"{product.name}" removed from wishlist.')
    return redirect("store:wishlist_list")
@require_POST
def ajax_wishlist_toggle(request):
    product_id = request.POST.get("product_id")
    if not product_id:
        return HttpResponseBadRequest("product_id required")
    try:
        product = Product.objects.get(pk=int(product_id))
    except Product.DoesNotExist:
        return JsonResponse({"success": False, "error": "Product not found"}, status=404)
    if request.user.is_authenticated:
        exists = Wishlist.objects.filter(user=request.user, product=product).exists()
        if exists:
            Wishlist.objects.filter(user=request.user, product=product).delete()
            action = "removed"
        else:
            Wishlist.objects.create(user=request.user, product=product)
            action = "added"
        count = Wishlist.objects.filter(user=request.user).count()
        return JsonResponse({"success": True, "action": action, "count": count})
    else:
        anon = request.session.get("anon_wishlist", [])
        if product.id in anon:
            anon.remove(product.id)
            action = "removed"
        else:
            anon.append(product.id)
            action = "added"
        request.session["anon_wishlist"] = anon
        return JsonResponse({"success": True, "action": action, "count": len(anon)})
@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    if Review.objects.filter(product=product, user=request.user).exists():
        return redirect("store:edit_review", slug=slug)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            rev = form.save(commit=False)
            rev.product = product
            rev.user = request.user
            rev.save()
            messages.success(request, "Review added!")
            return redirect(product.get_absolute_url())
    return render(request, "store/review_form.html", {
        "form": ReviewForm(),
        "product": product,
    })
@login_required
def edit_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    review = get_object_or_404(Review, product=product, user=request.user)
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated!")
            return redirect(product.get_absolute_url())
    return render(request, "store/review_form.html", {
        "form": ReviewForm(instance=review),
        "product": product,
    })
@login_required
def delete_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    Review.objects.filter(product=product, user=request.user).delete()
    messages.info(request, "Review deleted.")
    return redirect(product.get_absolute_url())
@login_required
def analytics_dashboard(request):
    if not request.user.is_staff:
        return redirect("store:product_list")
    total_products = Product.objects.filter(available=True).count()
    total_users = User.objects.count()
    total_orders = 0
    total_revenue = 0
    recent_orders = 0
    top_products = []
    try:
        from orders.models import Order, OrderItem
        total_orders = Order.objects.count()
        total_revenue = OrderItem.objects.aggregate(
            total=Sum(F("price") * F("quantity"), output_field=FloatField())
        )["total"] or 0
        last_30 = timezone.now() - timezone.timedelta(days=30)
        recent_orders = Order.objects.filter(created__gte=last_30).count()
        top_products = (
            OrderItem.objects.values("product__name")
            .annotate(qty=Sum("quantity"))
            .order_by("-qty")[:5]
        )
    except Exception:
        total_orders = 0
        total_revenue = 0
        recent_orders = 0
        top_products = []
    return render(request, "store/analytics_dashboard.html", {
        "total_products": total_products,
        "total_users": total_users,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "recent_orders": recent_orders,
        "top_products": top_products,
    })