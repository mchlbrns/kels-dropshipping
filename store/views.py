from django.shortcuts import render, get_object_or_404
from .models import Product, ProductImage, Order
from .forms import CheckoutForm

def get_or_create_demo_product():
    """Seeds a premium, high-converting demo product in the database if empty."""
    if Product.objects.exists():
        return Product.objects.filter(is_active=True).first()

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
        is_active=True
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

    return demo_product


def landing_page(request):
    """Renders the standard home page, auto-redirecting or rendering the first active product."""
    product = get_or_create_demo_product()
    if not product:
        return render(request, 'store/no_products.html')
        
    # Standard home renders the first active product landing page directly for conversions
    carousel_images = product.carousel_images.all()
    form = CheckoutForm()
    
    # Mock reviews to add social proof without third-party heavy apps
    social_proof_reviews = [
        {
            "name": "Mark D.",
            "rating": 5,
            "comment": "Absolutely phenomenal mouse! Extremely lightweight and the battery lasts for weeks. Delivered in just 2 days here in Manila!",
            "date": "May 18, 2026",
            "location": "Quezon City"
        },
        {
            "name": "Samantha P.",
            "rating": 5,
            "comment": "Super responsive and looks gorgeous on my white desk setup. The RGB lights are fully customizable. Highly recommended!",
            "date": "May 15, 2026",
            "location": "Cebu City"
        },
        {
            "name": "Jayson R.",
            "rating": 4,
            "comment": "Solid build quality, very light and clicks feel super clicky. Perfect for CS2 and coding sessions.",
            "date": "May 12, 2026",
            "location": "Davao City"
        }
    ]

    context = {
        'product': product,
        'carousel_images': carousel_images,
        'reviews': social_proof_reviews,
        'form': form,
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

    social_proof_reviews = [
        {
            "name": "Mark D.",
            "rating": 5,
            "comment": "Absolutely phenomenal mouse! Extremely lightweight and the battery lasts for weeks. Delivered in just 2 days here in Manila!",
            "date": "May 18, 2026",
            "location": "Quezon City"
        },
        {
            "name": "Samantha P.",
            "rating": 5,
            "comment": "Super responsive and looks gorgeous on my white desk setup. The RGB lights are fully customizable. Highly recommended!",
            "date": "May 15, 2026",
            "location": "Cebu City"
        },
        {
            "name": "Jayson R.",
            "rating": 4,
            "comment": "Solid build quality, very light and clicks feel super clicky. Perfect for CS2 and coding sessions.",
            "date": "May 12, 2026",
            "location": "Davao City"
        }
    ]

    context = {
        'product': product,
        'carousel_images': carousel_images,
        'reviews': social_proof_reviews,
        'form': form,
        'success': success,
        'order': order,
    }
    return render(request, 'store/landing_page.html', context)
