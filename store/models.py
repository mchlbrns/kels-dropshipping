from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

class Product(models.Model):
    title = models.CharField(
        max_length=255, 
        verbose_name="Product Title",
        help_text="Enter the consumer-facing name of the product"
    )
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name="Slug",
        help_text="Unique URL-friendly slug (auto-generated from title if left blank)"
    )
    description = models.TextField(
        blank=True, 
        default='', 
        verbose_name="Description",
        help_text="HTML or rich text describing the product and its benefits"
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Price (₱)",
        help_text="Selling price in Philippine Pesos (PHP)"
    )
    compare_at_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Compare at Price (₱)",
        help_text="Original price to show discounts or markdown (optional)"
    )
    cj_product_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        unique=True, 
        verbose_name="CJ Product ID",
        help_text="Unique product identifier from CJ Dropshipping for future API syncs"
    )
    video_url = models.URLField(
        blank=True, 
        null=True, 
        max_length=500,
        verbose_name="Video URL",
        help_text="Promotional video URL (e.g. YouTube, Vimeo, TikTok, or direct .mp4)"
    )
    features_list = models.JSONField(
        default=list, 
        blank=True, 
        verbose_name="Features List",
        help_text="Dynamic bullet points of features. Must be a JSON list, e.g. [\"Premium Material\", \"Waterproof\"]"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Toggle visibility on the landing page"
    )
    sku = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="SKU",
        help_text="Stock Keeping Unit code (optional)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.price is not None and self.price < 0:
            raise ValidationError({'price': "Price cannot be negative."})
        if self.compare_at_price is not None and self.compare_at_price < 0:
            raise ValidationError({'compare_at_price': "Compare at price cannot be negative."})
        if self.compare_at_price is not None and self.price is not None:
            if self.compare_at_price <= self.price:
                raise ValidationError({
                    'compare_at_price': "Compare at price should be higher than the current selling price to show a discount."
                })
        if not isinstance(self.features_list, list):
            raise ValidationError({'features_list': "Features list must be a JSON array/list."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure unique slug
            original_slug = self.slug
            queryset = Product.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            count = 1
            while queryset.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{count}"
                count += 1
        super().save(*args, **kwargs)

    @property
    def formatted_price(self):
        """Returns selling price formatted in Philippine Pesos (₱)."""
        return f"₱{self.price:,.2f}"

    @property
    def formatted_compare_at_price(self):
        """Returns compare-at price formatted in Philippine Pesos (₱) or None."""
        if self.compare_at_price:
            return f"₱{self.compare_at_price:,.2f}"
        return None

    @property
    def discount_percentage(self):
        """Calculates discount percentage between compare_at_price and price."""
        if self.compare_at_price and self.price and self.compare_at_price > self.price:
            discount = ((self.compare_at_price - self.price) / self.compare_at_price) * 100
            return round(discount)
        return 0


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='carousel_images', 
        verbose_name="Product"
    )
    image = models.ImageField(
        upload_to='products/carousel/', 
        blank=True, 
        null=True, 
        verbose_name="Local Image File",
        help_text="Upload an image file for the carousel"
    )
    image_url = models.URLField(
        blank=True, 
        null=True, 
        max_length=500, 
        verbose_name="External Image URL",
        help_text="Or specify an external image URL (useful for CJ Dropshipping imports)"
    )
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name="Display Order",
        help_text="Order in which images appear in the carousel (ascending)"
    )
    alt_text = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Alternative Text",
        help_text="Description of the image for SEO and screen readers"
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Image #{self.id} for {self.product.title} (Order: {self.order})"

    def clean(self):
        super().clean()
        if not self.image and not self.image_url:
            raise ValidationError("You must provide either an uploaded image file or an external image URL.")

    @property
    def get_url(self):
        """Returns the file URL or the external URL, depending on which is populated."""
        if self.image:
            return self.image.url
        return self.image_url or ''


class Order(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name="Product"
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name="Full Name"
    )
    phone_number = models.CharField(
        max_length=50,
        verbose_name="Mobile Number"
    )
    shipping_address = models.TextField(
        verbose_name="Complete Delivery Address"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Order Date"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.id} for {self.product.title} by {self.full_name}"
