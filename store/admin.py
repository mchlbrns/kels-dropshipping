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

    actions = ['duplicate_products', 'toggle_active_status', 'sync_with_cj']

    @admin.action(description="Sync selected products with CJ Dropshipping")
    def sync_with_cj(self, request, queryset):
        from store.dropshipping import CJDropshippingClient
        from django.conf import settings
        
        client = CJDropshippingClient(
            api_key=getattr(settings, 'CJ_API_KEY', ''),
            access_token=getattr(settings, 'CJ_ACCESS_TOKEN', ''),
            use_sandbox=getattr(settings, 'CJ_USE_SANDBOX', True)
        )
        
        success_count = 0
        failed_count = 0
        
        for product in queryset:
            if not product.cj_product_id:
                failed_count += 1
                continue
                
            res = client.sync_product(product.cj_product_id)
            if res.get('success'):
                product.sku = res.get('sku', product.sku)
                if 'price' in res:
                    product.price = res['price']
                if 'compare_at_price' in res:
                    product.compare_at_price = res['compare_at_price']
                product.save()
                success_count += 1
            else:
                failed_count += 1
                
        if success_count > 0:
            self.message_user(request, f"Successfully synchronized {success_count} product(s) with CJ.")
        if failed_count > 0:
            self.message_user(request, f"Failed to sync {failed_count} product(s) (missing CJ ID or API error).", level='WARNING')


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
    list_display = ('id', 'product', 'full_name', 'phone_number', 'fulfillment_status_badge', 'cj_order_id', 'created_at')
    list_filter = ('fulfillment_status', 'created_at', 'product')
    search_fields = ('full_name', 'phone_number', 'shipping_address', 'product__title', 'cj_order_id')
    readonly_fields = ('created_at', 'fulfilled_at', 'fulfillment_error')
    change_list_template = 'admin/store/order/change_list.html'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('product', 'created_at'),
        }),
        ('Customer Details', {
            'fields': ('full_name', 'phone_number', 'shipping_address'),
        }),
        ('CJ Dropshipping Sync', {
            'fields': ('fulfillment_status', 'cj_order_id', 'fulfillment_error', 'fulfilled_at'),
            'description': "Automated dropshipping integration and dispatch details."
        }),
    )

    actions = ['fulfill_with_cj']

    @admin.display(description="Fulfillment Status")
    def fulfillment_status_badge(self, obj):
        from django.utils.html import format_html
        colors = {
            'pending': ('#f59e0b', '#fef3c7', 'border-amber-200'),
            'fulfilled': ('#10b981', '#d1fae5', 'border-emerald-200'),
            'failed': ('#ef4444', '#fee2e2', 'border-red-200'),
        }
        color, bg, border = colors.get(obj.fulfillment_status, ('#6b7280', '#f3f4f6', 'border-gray-200'))
        return format_html(
            '<span class="px-2.5 py-0.5 rounded-full text-xs font-bold border" style="color: {}; background-color: {}; border-color: {}">{}</span>',
            color, bg, border, obj.get_fulfillment_status_display()
        )

    @admin.action(description="Fulfill selected orders with CJ Dropshipping")
    def fulfill_with_cj(self, request, queryset):
        from store.dropshipping import CJDropshippingClient
        from django.conf import settings
        from django.utils import timezone
        
        client = CJDropshippingClient(
            api_key=getattr(settings, 'CJ_API_KEY', ''),
            access_token=getattr(settings, 'CJ_ACCESS_TOKEN', ''),
            use_sandbox=getattr(settings, 'CJ_USE_SANDBOX', True)
        )
        
        success_count = 0
        failed_count = 0
        
        for order in queryset:
            if order.fulfillment_status == 'fulfilled':
                continue
                
            res = client.forward_order(order)
            if res.get('success'):
                order.fulfillment_status = 'fulfilled'
                order.cj_order_id = res.get('cj_order_id')
                order.fulfilled_at = timezone.now()
                order.fulfillment_error = None
                order.save()
                success_count += 1
            else:
                order.fulfillment_status = 'failed'
                order.fulfillment_error = res.get('error', 'Unknown error occurred')
                order.save()
                failed_count += 1
                
        if success_count > 0:
            self.message_user(request, f"Successfully fulfilled {success_count} order(s) via CJ Dropshipping.")
        if failed_count > 0:
            self.message_user(request, f"Failed to fulfill {failed_count} order(s). Check error details in order admin.", level='ERROR')


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
