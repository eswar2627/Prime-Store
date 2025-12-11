from django.contrib import admin
from django.contrib import messages
from .models import Order, OrderItem, Coupon


# --------------------------
# Coupon Admin
# --------------------------
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'discount_type',
        'discount_value',
        'min_amount',
        'valid_from',
        'valid_to',
        'active'
    )
    list_filter = ('active', 'discount_type')
    search_fields = ('code',)
    ordering = ('-valid_to',)


# --------------------------
# Order Item Inline
# --------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ('price', 'quantity')


# --------------------------
# Order Admin
# --------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'email',
        'first_name',
        'last_name',
        'status',
        'paid',
        'created',
        'tracking_number',
    ]

    list_filter = ['paid', 'status', 'created']
    search_fields = ['id', 'email', 'tracking_number']
    ordering = ['-created']
    inlines = [OrderItemInline]

    # Allow editing status directly in admin list
    list_editable = ('status',)

    # ------------------------------
    # ADMIN BULK ACTIONS
    # ------------------------------
    actions = [
        "mark_placed",
        "mark_packed",
        "mark_shipped",
        "mark_out_for_delivery",
        "mark_delivered",
    ]

    # Helper function to update and notify
    def _update_status(self, request, queryset, status_label):
        updated = queryset.update(status=status_label)
        self.message_user(
            request,
            f"{updated} order(s) successfully marked as {status_label.replace('_', ' ').title()}",
            messages.SUCCESS
        )

    def mark_placed(self, request, queryset):
        self._update_status(request, queryset, "PLACED")
    mark_placed.short_description = "Mark selected orders as PLACED"

    def mark_packed(self, request, queryset):
        self._update_status(request, queryset, "PACKED")
    mark_packed.short_description = "Mark selected orders as PACKED"

    def mark_shipped(self, request, queryset):
        self._update_status(request, queryset, "SHIPPED")
    mark_shipped.short_description = "Mark selected orders as SHIPPED"

    def mark_out_for_delivery(self, request, queryset):
        self._update_status(request, queryset, "OUT_FOR_DELIVERY")
    mark_out_for_delivery.short_description = "Mark selected orders as OUT FOR DELIVERY"

    def mark_delivered(self, request, queryset):
        self._update_status(request, queryset, "DELIVERED")
    mark_delivered.short_description = "Mark selected orders as DELIVERED"
