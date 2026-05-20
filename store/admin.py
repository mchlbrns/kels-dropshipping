from django.contrib import admin
from django.utils.safestring import mark_safe
from django.db import models
from .models import Product, ProductImage, Order, Review, FAQ

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


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1
    fields = ('name', 'rating', 'comment', 'location', 'is_approved')
    verbose_name = "Dynamic Review"
    verbose_name_plural = "Dynamic Reviews"


class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 1
    fields = ('question', 'answer', 'order')
    verbose_name = "Dynamic FAQ"
    verbose_name_plural = "Dynamic FAQs"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'slug',
        'formatted_price_display', 
        'sku', 
        'cj_product_id', 
        'is_active', 
        'is_featured',
        'carousel_image_count', 
        'created_at'
    )
    list_editable = ('is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured', 'created_at', 'updated_at')
    search_fields = ('title', 'slug', 'sku', 'cj_product_id', 'description')
    readonly_fields = ('created_at', 'updated_at', 'formatted_price_display')
    prepopulated_fields = {'slug': ('title',)}
    
    inlines = [ProductImageInline, ReviewInline, FAQInline]

    fieldsets = (
        ('General Information', {
            'fields': ('title', 'slug', 'sku', 'description', ('is_active', 'is_featured')),
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
            reviews = list(product.reviews.all())
            faqs = list(product.faqs.all())
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
            for rev in reviews:
                Review.objects.create(
                    product=product,
                    name=rev.name,
                    rating=rev.rating,
                    comment=rev.comment,
                    location=rev.location,
                    is_approved=rev.is_approved
                )
            for f in faqs:
                FAQ.objects.create(
                    product=product,
                    question=f.question,
                    answer=f.answer,
                    order=f.order
                )
        self.message_user(request, f"Successfully duplicated {queryset.count()} product(s).")

    @admin.action(description="Toggle active status")
    def toggle_active_status(self, request, queryset):
        for product in queryset:
            product.is_active = not product.is_active
            product.save()
        self.message_user(request, f"Successfully toggled active status for {queryset.count()} product(s).")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'rating', 'location', 'is_approved', 'created_at')
    list_editable = ('is_approved',)
    list_filter = ('is_approved', 'rating', 'created_at', 'product')
    search_fields = ('name', 'comment', 'location', 'product__title')
    readonly_fields = ('created_at',)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'product', 'order')
    list_editable = ('order',)
    list_filter = ('product',)
    search_fields = ('question', 'answer', 'product__title')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'full_name', 'phone_number', 'created_at')
    list_filter = ('created_at', 'product')
    search_fields = ('full_name', 'phone_number', 'shipping_address', 'product__title')
    readonly_fields = ('created_at',)
    change_list_template = 'admin/store/order/change_list.html'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('product', 'created_at'),
        }),
        ('Customer Details', {
            'fields': ('full_name', 'phone_number', 'shipping_address'),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        
        # Check if response has context_data (Standard TemplateResponse)
        if hasattr(response, 'context_data'):
            cl = response.context_data.get('cl')
            if cl:
                # cl.queryset contains the current filtered queryset!
                queryset = cl.queryset
                
                # Compute total orders
                total_orders = queryset.count()
                
                # Compute total revenue
                total_revenue = queryset.aggregate(total=models.Sum('product__price'))['total'] or 0
                
                # Product-by-product sales breakdown
                product_stats = queryset.values('product__title', 'product__price').annotate(
                    order_count=models.Count('id')
                ).order_by('-order_count')
                
                breakdown = []
                for stat in product_stats:
                    title = stat['product__title']
                    price = stat['product__price']
                    count = stat['order_count']
                    rev = price * count
                    breakdown.append({
                        'title': title,
                        'price': f"₱{price:,.2f}",
                        'count': count,
                        'revenue': f"₱{rev:,.2f}"
                    })
                
                formatted_revenue = f"₱{total_revenue:,.2f}"
                
                response.context_data['sales_dashboard'] = {
                    'total_orders': total_orders,
                    'total_revenue': formatted_revenue,
                    'breakdown': breakdown,
                }
        return response
