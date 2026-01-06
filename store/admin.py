from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name', 'slug']
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    readonly_fields = ["image_preview"]
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="90" style="border-radius:4px;" />',
                obj.image.url
            )
        return ""
    image_preview.short_description = "Preview"
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'brand',
        'price',
        'storage_capacity',
        'ram_size',
        'cpu_model',
        'stock',
        'available',
        'created'
    ]
    list_filter = [
        'available',
        'created',
        'brand',
        'category',
        'operating_system'
    ]
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ("🟦 Basic Information", {
            "fields": (
                "name",
                "slug",
                "category",
                "price",
                "image",
                "description",
                "about_this_item",
            )
        }),
        ("🟩 Electronics Specifications", {
            "fields": (
                "brand",
                "model_name",
                "colour",
                "screen_size",
                "storage_capacity",
                "hard_disk_size",
                "ram_size",
                "cpu_model",
                "operating_system",
                "graphics_card",
                "graphics_coprocessor",
            )
        }),
        ("🟪 Clothing & Fashion Specifications", {
            "fields": (
                "material_composition",
                "style",
                "fit_type",
                "length",
                "pattern",
                "care_instructions",
                "country_of_origin",
            )
        }),
        ("🟥 Inventory", {
            "fields": ("stock", "available")
        }),
    )
    inlines = [ProductImageInline]