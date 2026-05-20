from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Product, ProductImage, Order

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('image', 'image_url', 'image_preview', 'order', 'alt_text')
    readonly_fields = ('image_preview',)
    ordering = ('order',)

    def image_preview(self, obj):
        url = obj.get_url
        if url:
            return mark_safe(f'<img src="{url}" style="max-height: 80px; max-width: 80px; border-radius: 4px; object-fit: cover;" />')
        return "No Image"
    
    image_preview.short_description = "Preview"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'slug',
        'formatted_price_display', 
        'sku', 
        'cj_product_id', 
        'is_active', 
        'carousel_image_count', 
        'created_at'
    )
    list_editable = ('is_active',)
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('title', 'slug', 'sku', 'cj_product_id', 'description')
    readonly_fields = ('created_at', 'updated_at', 'formatted_price_display')
    prepopulated_fields = {'slug': ('title',)}
    
    inlines = [ProductImageInline]

    fieldsets = (
        ('General Information', {
            'fields': ('title', 'slug', 'sku', 'description', 'is_active'),
            'description': "Configure basic product details and URL slug displayed on the landing page."
        }),
        ('Pricing Options', {
            'fields': (('price', 'compare_at_price'), 'formatted_price_display'),
            'description': "Set the customer-facing selling price and the original compare-at price to show discounts."
        }),
        ('Media & External Syncing', {
            'fields': ('video_url', 'cj_product_id'),
            'description': "Provide links to TikTok/YouTube promotional videos and sync keys for CJ Dropshipping."
        }),
        ('Dynamic Product Features', {
            'fields': ('features_list',),
            'description': "Input dynamic bullet points for features in JSON format (e.g. [\"Feature A\", \"Feature B\"])."
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['duplicate_products', 'toggle_active_status']

    @admin.display(description="Price (₱)")
    def formatted_price_display(self, obj):
        return obj.formatted_price

    @admin.display(description="Carousel Images")
    def carousel_image_count(self, obj):
        return obj.carousel_images.count()

    @admin.action(description="Duplicate selected products")
    def duplicate_products(self, request, queryset):
        for product in queryset:
            images = list(product.carousel_images.all())
            product.pk = None
            product.title = f"{product.title} (Copy)"
            product.slug = None # will auto-generate from new title in save()
            if product.cj_product_id:
                product.cj_product_id = f"{product.cj_product_id}-COPY"
            product.save()
            
            for img in images:
                ProductImage.objects.create(
                    product=product,
                    image=img.image,
                    image_url=img.image_url,
                    order=img.order,
                    alt_text=img.alt_text
                )
        self.message_user(request, f"Successfully duplicated {queryset.count()} product(s).")

    @admin.action(description="Toggle active status")
    def toggle_active_status(self, request, queryset):
        for product in queryset:
            product.is_active = not product.is_active
            product.save()
        self.message_user(request, f"Successfully toggled active status for {queryset.count()} product(s).")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'full_name', 'phone_number', 'created_at')
    list_filter = ('created_at', 'product')
    search_fields = ('full_name', 'phone_number', 'shipping_address', 'product__title')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Order Information', {
            'fields': ('product', 'created_at'),
        }),
        ('Customer Details', {
            'fields': ('full_name', 'phone_number', 'shipping_address'),
        }),
    )
