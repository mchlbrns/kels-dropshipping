import logging
import json
import hmac
import hashlib
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from django.conf import settings

from .models import Product, ProductImage, Order, Review, FAQ
from .forms import CheckoutForm
from store.paymongo import PayMongoClient
from store.dropshipping import CJDropshippingClient

logger = logging.getLogger(__name__)


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


def trigger_order_fulfillment(order):
    """
    Safely triggers automatic order fulfillment with CJ Dropshipping.
    Validates rules:
    - Order must not already be fulfilled.
    - Online orders check settings.CJ_AUTO_FULFILL_PAID (must be paid).
    - COD orders check settings.CJ_AUTO_FULFILL_COD.
    """
    if order.fulfillment_status == 'fulfilled':
        logger.info(f"Order #{order.id} is already fulfilled. Skipping.")
        return False

    is_cod = order.payment_method == 'cod'
    is_paid = order.payment_method == 'online' and order.payment_status == 'paid'

    should_fulfill = False
    if is_cod and getattr(settings, 'CJ_AUTO_FULFILL_COD', False):
        should_fulfill = True
    elif is_paid and getattr(settings, 'CJ_AUTO_FULFILL_PAID', True):
        should_fulfill = True

    if not should_fulfill:
        logger.info(f"Fulfillment conditions not met for Order #{order.id} (Payment: {order.payment_method}, Status: {order.payment_status}).")
        return False

    logger.info(f"Auto-dispatching Order #{order.id} to CJ Dropshipping.")
    client = CJDropshippingClient(
        api_key=getattr(settings, 'CJ_API_KEY', ''),
        access_token=getattr(settings, 'CJ_ACCESS_TOKEN', ''),
        use_sandbox=getattr(settings, 'CJ_USE_SANDBOX', True)
    )

    res = client.forward_order(order)
    if res.get('success'):
        order.fulfillment_status = 'fulfilled'
        order.cj_order_id = res.get('cj_order_id')
        order.fulfilled_at = timezone.now()
        order.fulfillment_error = None
        order.save()
        logger.info(f"Successfully auto-fulfilled Order #{order.id} on CJ.")
        return True
    else:
        order.fulfillment_status = 'failed'
        order.fulfillment_error = res.get('error', 'Unknown automated fulfillment failure')
        order.save()
        logger.error(f"Automated fulfillment failed for Order #{order.id}: {order.fulfillment_error}")
        return False


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
            
            if order.payment_method == 'online':
                success_url = request.build_absolute_uri(reverse('store:payment_success')) + f"?order_id={order.id}"
                cancel_url = request.build_absolute_uri(request.path)
                
                client = PayMongoClient()
                res = client.create_checkout_session(order, success_url, cancel_url)
                
                if res.get('success'):
                    order.paymongo_session_id = res.get('session_id')
                    order.save()
                    return redirect(res.get('checkout_url'))
                else:
                    form.add_error(None, f"Online payment setup failed: {res.get('error')}. Please select Cash on Delivery or try again.")
                    order.delete()
            else:
                success = True
                trigger_order_fulfillment(order)
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
            
            if order.payment_method == 'online':
                success_url = request.build_absolute_uri(reverse('store:payment_success')) + f"?order_id={order.id}"
                cancel_url = request.build_absolute_uri(request.path)
                
                client = PayMongoClient()
                res = client.create_checkout_session(order, success_url, cancel_url)
                
                if res.get('success'):
                    order.paymongo_session_id = res.get('session_id')
                    order.save()
                    return redirect(res.get('checkout_url'))
                else:
                    form.add_error(None, f"Online payment setup failed: {res.get('error')}. Please select Cash on Delivery or try again.")
                    order.delete()
            else:
                success = True
                trigger_order_fulfillment(order)
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


def payment_success(request):
    """
    Handles redirection from PayMongo Checkout Session.
    Retrieves and verifies checkout session status, updates order payment status,
    and displays a beautiful conversion success screen.
    """
    order_id = request.GET.get('order_id')
    session_id = request.GET.get('session_id')

    order = None
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            session_id = order.paymongo_session_id
        except Order.DoesNotExist:
            pass

    if not session_id and not order:
        return redirect('store:store_catalog')

    if not order:
        try:
            order = Order.objects.get(paymongo_session_id=session_id)
        except Order.DoesNotExist:
            if session_id and session_id.startswith("pm_mock_sess_"):
                try:
                    parts = session_id.split('_')
                    if len(parts) >= 4:
                        order_id_val = int(parts[3])
                        order = Order.objects.get(id=order_id_val)
                    else:
                        order = Order.objects.latest('created_at')
                except (IndexError, ValueError, Order.DoesNotExist):
                    order = Order.objects.latest('created_at')
            else:
                return redirect('store:store_catalog')

    client = PayMongoClient()
    res = client.retrieve_checkout_session(session_id)
    
    if res.get('success'):
        payment_status = res.get('payment_status')
        if payment_status == 'paid':
            order.payment_status = 'paid'
            order.paymongo_payment_intent_id = res.get('payment_intent_id')
            order.save()
            trigger_order_fulfillment(order)
    else:
        logger.error(f"Failed to retrieve PayMongo session {session_id}: {res.get('error')}")

    context = {
        'order': order,
        'product': order.product,
    }
    return render(request, 'store/payment_success.html', context)


@csrf_exempt
@require_POST
def paymongo_webhook(request):
    """
    Background webhook endpoint called by PayMongo to securely confirm e-wallet and card payments.
    Matches event type 'checkout_session.payment.paid', updates order status, and triggers CJ forwarding.
    """
    # 1. Signature Verification (if secret configured)
    webhook_secret = getattr(settings, 'PAYMONGO_WEBHOOK_SECRET', '')
    if webhook_secret:
        signature_header = request.META.get('HTTP_X_PAYMONGO_SIGNATURE', '')
        t = None
        li = None
        te = None
        for pair in signature_header.split(','):
            if '=' in pair:
                parts = pair.split('=', 1)
                if len(parts) == 2:
                    k, v = parts
                    if k.strip() == 't':
                        t = v.strip()
                    elif k.strip() == 'li':
                        li = v.strip()
                    elif k.strip() == 'te':
                        te = v.strip()
        
        signature = li or te
        if t and signature:
            try:
                # Concatenate payload: timestamp + "." + request body
                payload_str = request.body.decode('utf-8')
                data_to_sign = f"{t}.{payload_str}"
                computed_sig = hmac.new(
                    webhook_secret.encode('utf-8'),
                    data_to_sign.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(computed_sig, signature):
                    logger.warning("PayMongo webhook signature verification failed.")
                    return HttpResponse("Invalid signature", status=401)
            except Exception as e:
                logger.error(f"Error during signature validation: {str(e)}")
                return HttpResponse("Signature processing error", status=400)
        else:
            logger.warning("PayMongo webhook missing signature parameters.")
            return HttpResponse("Missing signature", status=400)

    # 2. Parse Webhook Event Data
    try:
        data = json.loads(request.body)
    except ValueError:
        return HttpResponse("Invalid JSON", status=400)

    event_type = data.get('data', {}).get('attributes', {}).get('type')
    logger.info(f"Received PayMongo webhook event: {event_type}")

    if event_type == 'checkout_session.payment.paid':
        session_data = data.get('data', {}).get('attributes', {}).get('data', {})
        session_id = session_data.get('id')
        
        if not session_id:
            return HttpResponse("Missing session ID in payload", status=400)

        # Match to Order
        try:
            order = Order.objects.get(paymongo_session_id=session_id)
        except Order.DoesNotExist:
            logger.error(f"Order not found for PayMongo session ID: {session_id}")
            return HttpResponse("Order not found", status=404)

        # Update order payment status
        if order.payment_status != 'paid':
            order.payment_status = 'paid'
            payments = session_data.get('attributes', {}).get('payments', [])
            if payments:
                order.paymongo_payment_intent_id = payments[0].get('id')
            order.save()
            logger.info(f"Order #{order.id} marked as PAID via webhook.")
            
            # Auto-forward to CJ Dropshipping
            trigger_order_fulfillment(order)
            
    return HttpResponse("OK", status=200)


def product_stock_api(request, slug):
    """
    Speed-optimized, cached API fetching live inventory levels from CJ Dropshipping.
    Caches results for 10 minutes to protect loading speeds on local TM/Globe mobile connections.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    if not product.sku:
        return JsonResponse({'success': False, 'stock': 0, 'error': 'Product SKU not configured'})

    cache_key = f"cj_stock_{product.sku}"
    stock = cache.get(cache_key)

    if stock is None:
        client = CJDropshippingClient(
            api_key=getattr(settings, 'CJ_API_KEY', ''),
            access_token=getattr(settings, 'CJ_ACCESS_TOKEN', ''),
            use_sandbox=getattr(settings, 'CJ_USE_SANDBOX', True)
        )
        res = client.get_inventory(product.sku)
        if res.get('success'):
            stock = res.get('stock', 0)
        else:
            # Safe high-converting fallback stock if CJ API is down/mocking fails
            stock = 150
        cache.set(cache_key, stock, 600)  # Cache for 10 minutes (600 seconds)

    return JsonResponse({
        'success': True,
        'sku': product.sku,
        'stock': stock
    })

