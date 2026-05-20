from django.shortcuts import render, get_object_or_404
from .models import Product, ProductImage, Order, Review, FAQ
from .forms import CheckoutForm

def get_or_create_demo_product():
    """Seeds a premium, high-converting demo product and dynamic assets if empty."""
    if Product.objects.exists():
        featured = Product.objects.filter(is_active=True, is_featured=True).first()
        product = featured or Product.objects.filter(is_active=True).first()
        if product:
            # Ensure reviews and FAQs are seeded for the existing product
            if not product.reviews.exists():
                Review.objects.create(
                    product=product,
                    name="Mark D.",
                    rating=5,
                    comment="Absolutely phenomenal mouse! Extremely lightweight and the battery lasts for weeks. Delivered in just 2 days here in Manila!",
                    location="Quezon City"
                )
                Review.objects.create(
                    product=product,
                    name="Samantha P.",
                    rating=5,
                    comment="Super responsive and looks gorgeous on my white desk setup. The RGB lights are fully customizable. Highly recommended!",
                    location="Cebu City"
                )
                Review.objects.create(
                    product=product,
                    name="Jayson R.",
                    rating=4,
                    comment="Solid build quality, very light and clicks feel super clicky. Perfect for CS2 and coding sessions.",
                    location="Davao City"
                )
            if not product.faqs.exists():
                FAQ.objects.create(
                    product=product,
                    question="How does Cash on Delivery (COD) work?",
                    answer="Cash on Delivery is 100% risk-free. You only prepare the exact payment amount and hand it directly to our courier rider once the package is delivered to your doorstep. No downpayment or bank account required!",
                    order=1
                )
                FAQ.objects.create(
                    product=product,
                    question="Is shipping really free and are there hidden fees?",
                    answer="Yes, shipping is 100% free and fully insured nationwide. The price you see on this page is the exact amount you will pay upon delivery. There are absolutely no hidden charges.",
                    order=2
                )
                FAQ.objects.create(
                    product=product,
                    question="Can I inspect the item before paying?",
                    answer="Under courier policies in the Philippines, riders cannot open packages before payment is received. However, we cover every order with a 7-Day Replacement Guarantee if there are any defects.",
                    order=3
                )
                FAQ.objects.create(
                    product=product,
                    question="How do I track my order?",
                    answer="Once your order is processed and shipped, our automated system will send you a SMS tracking link to follow your parcel's journey from our global center straight to your doorstep.",
                    order=4
                )
            return product

    # Create the demo product
    demo_product = Product.objects.create(
        title="AeroGlide Max Pro - Ergonomic Wireless Gaming Mouse",
        sku="AG-MAX-PRO-01",
        description=(
            "<p>Elevate your productivity and gameplay with the <strong>AeroGlide Max Pro</strong>. "
            "Engineered with a state-of-the-art optical sensor, hybrid wireless connectivity, and an "
            "ultra-lightweight honeycomb shell, this mouse delivers lag-free responsiveness and "
            "pixel-perfect accuracy for high-intensity setups.</p>"
            "<p>Perfect for remote developers, creative professionals, and competitive gamers who "
            "demand speed, comfort, and unmatched battery endurance.</p>"
        ),
        price=1899.00,
        compare_at_price=2999.00,
        cj_product_id="CJ-9928371-M",
        video_url="https://www.w3schools.com/html/mov_bbb.mp4", # standard public sample video file
        features_list=[
            "Ultra-lightweight 58g ergonomic honeycomb casing",
            "PixArt 3395 26,000 DPI high-performance optical sensor",
            "Dual-mode connectivity: 2.4GHz lag-free wireless & Bluetooth",
            "Up to 80 hours of continuous high-intensity battery life",
            "Vibrant dynamic RGB customizable lighting zones with 16.8M colors"
        ],
        is_active=True,
        is_featured=True
    )

    # Seed 3 high-quality Unsplash image URLs to build a premium carousel
    ProductImage.objects.create(
        product=demo_product,
        image_url="https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=800&auto=format&fit=crop",
        order=1,
        alt_text="AeroGlide Max Pro sleek design top view"
    )
    ProductImage.objects.create(
        product=demo_product,
        image_url="https://images.unsplash.com/photo-1625842268584-8f3290447036?w=800&auto=format&fit=crop",
        order=2,
        alt_text="Side view featuring premium customizable grip"
    )
    ProductImage.objects.create(
        product=demo_product,
        image_url="https://images.unsplash.com/photo-1527814050087-3b952115a601?w=800&auto=format&fit=crop",
        order=3,
        alt_text="RGB lighting highlight under dark setup"
    )

    # Seed dynamic social proof reviews
    Review.objects.create(
        product=demo_product,
        name="Mark D.",
        rating=5,
        comment="Absolutely phenomenal mouse! Extremely lightweight and the battery lasts for weeks. Delivered in just 2 days here in Manila!",
        location="Quezon City"
    )
    Review.objects.create(
        product=demo_product,
        name="Samantha P.",
        rating=5,
        comment="Super responsive and looks gorgeous on my white desk setup. The RGB lights are fully customizable. Highly recommended!",
        location="Cebu City"
    )
    Review.objects.create(
        product=demo_product,
        name="Jayson R.",
        rating=4,
        comment="Solid build quality, very light and clicks feel super clicky. Perfect for CS2 and coding sessions.",
        location="Davao City"
    )

    # Seed dynamic FAQs
    FAQ.objects.create(
        product=demo_product,
        question="How does Cash on Delivery (COD) work?",
        answer="Cash on Delivery is 100% risk-free. You only prepare the exact payment amount and hand it directly to our courier rider once the package is delivered to your doorstep. No downpayment or bank account required!",
        order=1
    )
    FAQ.objects.create(
        product=demo_product,
        question="Is shipping really free and are there hidden fees?",
        answer="Yes, shipping is 100% free and fully insured nationwide. The price you see on this page is the exact amount you will pay upon delivery. There are absolutely no hidden charges.",
        order=2
    )
    FAQ.objects.create(
        product=demo_product,
        question="Can I inspect the item before paying?",
        answer="Under courier policies in the Philippines, riders cannot open packages before payment is received. However, we cover every order with a 7-Day Replacement Guarantee if there are any defects.",
        order=3
    )
    FAQ.objects.create(
        product=demo_product,
        question="How do I track my order?",
        answer="Once your order is processed and shipped, our automated system will send you a SMS tracking link to follow your parcel's journey from our global center straight to your doorstep.",
        order=4
    )

    return demo_product


def landing_page(request):
    """Renders the standard home page, support GET/POST, auto-redirecting or rendering the featured/first active product."""
    product = Product.objects.filter(is_active=True, is_featured=True).first()
    if not product:
        product = Product.objects.filter(is_active=True).first()
    if not product:
        # Fall back to seeding the demo product (which is featured)
        product = get_or_create_demo_product()
        
    if not product:
        return render(request, 'store/no_products.html')
        
    carousel_images = product.carousel_images.all()
    success = False
    order = None

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.product = product
            order.save()
            success = True
            form = CheckoutForm() # Reset form upon successful order
    else:
        form = CheckoutForm()
    
    # Load dynamic reviews and FAQs
    reviews = product.reviews.filter(is_approved=True)
    faqs = product.faqs.all()

    context = {
        'product': product,
        'carousel_images': carousel_images,
        'reviews': reviews,
        'faqs': faqs,
        'form': form,
        'success': success,
        'order': order,
    }
    return render(request, 'store/landing_page.html', context)


def product_detail(request, slug):
    """Renders a dynamic product landing page based on the product slug."""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    carousel_images = product.carousel_images.all()
    success = False
    order = None

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.product = product
            order.save()
            success = True
            form = CheckoutForm() # Reset form upon successful order
    else:
        form = CheckoutForm()

    # Load dynamic reviews and FAQs
    reviews = product.reviews.filter(is_approved=True)
    faqs = product.faqs.all()

    context = {
        'product': product,
        'carousel_images': carousel_images,
        'reviews': reviews,
        'faqs': faqs,
        'form': form,
        'success': success,
        'order': order,
    }
    return render(request, 'store/landing_page.html', context)


def store_catalog(request):
    """Renders the catalog page showing all active products."""
    products = Product.objects.filter(is_active=True)
    # Ensure there's at least one product
    if not products.exists():
        get_or_create_demo_product()
        products = Product.objects.filter(is_active=True)
        
    context = {
        'products': products,
    }
    return render(request, 'store/catalog.html', context)
