from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from store.models import Product, Order, Review, FAQ
from store.forms import CheckoutForm
from store.dropshipping import CJDropshippingClient
from django.contrib.auth.models import User

class StoreModelTestCase(TestCase):
    def setUp(self):
        self.p1 = Product.objects.create(
            title="Product One",
            price=100.00,
            compare_at_price=150.00,
            is_active=True,
            is_featured=True,
            features_list=["Feature One", "Feature Two"]
        )
        self.p2 = Product.objects.create(
            title="Product Two",
            price=200.00,
            compare_at_price=250.00,
            is_active=True,
            is_featured=False
        )

    def test_single_featured_product(self):
        """Test that setting a product as featured automatically un-features all others."""
        self.assertTrue(self.p1.is_featured)
        self.assertFalse(self.p2.is_featured)

        # Set p2 as featured
        self.p2.is_featured = True
        self.p2.save()

        # Refresh from db
        self.p1.refresh_from_db()
        self.p2.refresh_from_db()

        self.assertFalse(self.p1.is_featured)
        self.assertTrue(self.p2.is_featured)

    def test_product_clean_pricing(self):
        """Test pricing clean validation."""
        p = Product(title="Bad Price", price=-10.00)
        with self.assertRaises(ValidationError):
            p.clean()

        p2 = Product(title="Bad Compare Price", price=100, compare_at_price=50)
        with self.assertRaises(ValidationError):
            p2.clean()

    def test_product_none_pricing(self):
        """Test that properties handle None values gracefully for new unsaved objects."""
        p = Product(title="New Product")
        self.assertEqual(p.formatted_price, "₱0.00")
        self.assertIsNone(p.formatted_compare_at_price)
        self.assertEqual(p.discount_percentage, 0)

    def test_review_creation_and_stars_display(self):
        """Test review creation and star display formatting."""
        r = Review.objects.create(
            product=self.p1,
            name="Test Reviewer",
            rating=5,
            comment="Awesome product",
            location="Quezon City"
        )
        self.assertEqual(r.stars_display, "★★★★★")
        
        # Invalid rating
        r_bad = Review(product=self.p1, name="Bad", rating=6, comment="Bad")
        with self.assertRaises(ValidationError):
            r_bad.clean()

    def test_faq_ordering(self):
        """Test FAQ sorting order."""
        f2 = FAQ.objects.create(product=self.p1, question="Q2?", answer="A2", order=2)
        f1 = FAQ.objects.create(product=self.p1, question="Q1?", answer="A1", order=1)
        
        faqs = list(self.p1.faqs.all())
        self.assertEqual(faqs[0], f1)
        self.assertEqual(faqs[1], f2)


class StoreViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.p = Product.objects.create(
            title="Featured Product",
            price=500.00,
            compare_at_price=800.00,
            is_active=True,
            is_featured=True,
            features_list=["Premium Material"]
        )
        # Create review and FAQ for p
        self.r = Review.objects.create(
            product=self.p,
            name="Mark",
            rating=5,
            comment="Great!",
            location="Manila"
        )
        self.f = FAQ.objects.create(
            product=self.p,
            question="Shipping time?",
            answer="10-15 days",
            order=1
        )

    def test_landing_page_get(self):
        """Test landing page loads featured product dynamically."""
        response = self.client.get(reverse('store:landing_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Featured Product")
        self.assertContains(response, "₱500.00")
        self.assertContains(response, "Mark")
        self.assertContains(response, "Shipping time?")

    def test_landing_page_post_success(self):
        """Test order submission via POST on landing page."""
        post_data = {
            'full_name': 'Juan Dela Cruz',
            'phone_number': '09171234567',
            'shipping_address': '123 Rizal St, Brgy 1, Pasay City'
        }
        response = self.client.post(reverse('store:landing_page'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['success'])
        
        # Verify order created
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.full_name, 'Juan Dela Cruz')
        self.assertEqual(order.phone_number, '09171234567')
        self.assertEqual(order.product, self.p)

    def test_landing_page_post_invalid_phone(self):
        """Test invalid Philippine phone number fails validation."""
        post_data = {
            'full_name': 'Juan Dela Cruz',
            'phone_number': '1234567890', # invalid
            'shipping_address': '123 Rizal St, Brgy 1, Pasay City'
        }
        response = self.client.post(reverse('store:landing_page'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['success'])
        self.assertEqual(Order.objects.count(), 0)

    def test_product_detail_view(self):
        """Test that subpage details load correctly and handle order capture."""
        p_sub = Product.objects.create(
            title="Sub Product",
            price=299.00,
            compare_at_price=399.00,
            is_active=True,
            is_featured=False
        )
        response = self.client.get(reverse('store:product_detail', args=[p_sub.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sub Product")

        # Submit order on subpage
        post_data = {
            'full_name': 'Pedro Penduko',
            'phone_number': '09187654321',
            'shipping_address': 'Baguio City'
        }
        response = self.client.post(reverse('store:product_detail', args=[p_sub.slug]), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['success'])
        self.assertEqual(Order.objects.filter(product=p_sub).count(), 1)

    def test_store_catalog_view(self):
        """Test store catalog listing."""
        response = self.client.get(reverse('store:store_catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Featured Product")


class StoreDropshippingClientTestCase(TestCase):
    def test_mock_fulfillment_and_inventory(self):
        client = CJDropshippingClient(use_sandbox=True)
        
        # Test inventory check
        stock_res = client.get_inventory("SKU-123")
        self.assertTrue(stock_res['success'])
        self.assertIn('stock', stock_res)
        
        # Test sync product
        sync_res = client.sync_product("CJ-123")
        self.assertTrue(sync_res['success'])
        self.assertEqual(sync_res['sku'], "AG-MAX-PRO-01")


class AdminDashboardTestCase(TestCase):
    def setUp(self):
        self.super_user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.p1 = Product.objects.create(
            title="Mouse", price=1000.00, is_active=True
        )
        self.p2 = Product.objects.create(
            title="Keyboard", price=2000.00, is_active=True
        )
        # Create orders
        Order.objects.create(product=self.p1, full_name="A", phone_number="09171112222", shipping_address="Manila")
        Order.objects.create(product=self.p1, full_name="B", phone_number="09171112222", shipping_address="Manila")
        Order.objects.create(product=self.p2, full_name="C", phone_number="09171112222", shipping_address="Manila")

    def test_order_changelist_dashboard_metrics(self):
        """Test that OrderAdmin changelist calculates total revenue, total orders, and breakdowns."""
        self.client.force_login(self.super_user)
        response = self.client.get(reverse('admin:store_order_changelist'))
        self.assertEqual(response.status_code, 200)
        
        # Check sales_dashboard in context
        self.assertIn('sales_dashboard', response.context)
        dashboard = response.context['sales_dashboard']
        
        # Total revenue: 1000*2 + 2000*1 = 4000
        self.assertEqual(dashboard['total_orders'], 3)
        self.assertEqual(dashboard['total_revenue'], "₱4,000.00")
        
        # Breakdown checks
        breakdown = dashboard['breakdown']
        self.assertEqual(len(breakdown), 2)
        # Sort by count is descending, so "Mouse" should be first (2 orders)
        self.assertEqual(breakdown[0]['title'], "Mouse")
        self.assertEqual(breakdown[0]['count'], 2)
        self.assertEqual(breakdown[0]['revenue'], "₱2,000.00")
        
        self.assertEqual(breakdown[1]['title'], "Keyboard")
        self.assertEqual(breakdown[1]['count'], 1)
        self.assertEqual(breakdown[1]['revenue'], "₱2,000.00")


from store.admin import OrderAdmin, ProductAdmin
from django.contrib.admin.sites import AdminSite

@override_settings(CJ_USE_SANDBOX=True)
class OrderFulfillmentFidelityTestCase(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.product = Product.objects.create(
            title="Promo Mouse",
            price=1500.00,
            sku="PM-01",
            cj_product_id="CJ-TEST-ID",
            is_active=True
        )
        self.order = Order.objects.create(
            product=self.product,
            full_name="Maria Santos",
            phone_number="09187654321",
            shipping_address="Quezon City, Metro Manila"
        )

    def test_default_fulfillment_status(self):
        """Verify new orders have pending status."""
        self.assertEqual(self.order.fulfillment_status, 'pending')
        self.assertIsNone(self.order.cj_order_id)
        self.assertIsNone(self.order.fulfilled_at)
        self.assertIsNone(self.order.fulfillment_error)

    def test_order_admin_fulfillment_action(self):
        """Verify the OrderAdmin fulfill_with_cj action works."""
        order_admin = OrderAdmin(Order, self.site)
        queryset = Order.objects.filter(id=self.order.id)
        
        # Mock message_user to avoid message storage configuration errors
        messages_received = []
        order_admin.message_user = lambda request, message, level='INFO', **kwargs: messages_received.append((message, level))
        
        class MockRequest:
            pass
        req = MockRequest()
        
        order_admin.fulfill_with_cj(req, queryset)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.fulfillment_status, 'fulfilled')
        self.assertIsNotNone(self.order.cj_order_id)
        self.assertIsNotNone(self.order.fulfilled_at)
        self.assertIsNone(self.order.fulfillment_error)
        self.assertEqual(len(messages_received), 1)

    def test_product_admin_sync_action(self):
        """Verify the ProductAdmin sync_with_cj action works."""
        product_admin = ProductAdmin(Product, self.site)
        queryset = Product.objects.filter(id=self.product.id)
        
        # Mock message_user to avoid message storage configuration errors
        messages_received = []
        product_admin.message_user = lambda request, message, level='INFO', **kwargs: messages_received.append((message, level))
        
        class MockRequest:
            pass
        req = MockRequest()
        
        self.product.price = 500.00
        self.product.save()
        
        product_admin.sync_with_cj(req, queryset)
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, 1899.00)
        self.assertEqual(self.product.sku, "AG-MAX-PRO-01")
        self.assertEqual(len(messages_received), 1)


@override_settings(PAYMONGO_SECRET_KEY='pm_mock_secret_key', PAYMONGO_WEBHOOK_SECRET='')
class StorePayMongoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            title="AeroGlide Max Pro",
            price=1899.00,
            sku="AG-MAX-PRO-01",
            is_active=True,
            is_featured=True
        )

    def test_checkout_form_with_payment_method(self):
        """Verify CheckoutForm initializes payment_method field correctly."""
        form = CheckoutForm()
        self.assertIn('payment_method', form.fields)

    def test_online_payment_redirects_to_paymongo(self):
        """Verify that choosing 'online' payment redirects the customer to PayMongo (mock url)."""
        post_data = {
            'full_name': 'Pedro Penduko',
            'phone_number': '09187654321',
            'shipping_address': 'Baguio City',
            'payment_method': 'online'
        }
        response = self.client.post(reverse('store:landing_page'), post_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/order/payment-success/?order_id=', response.url)
        
        order = Order.objects.latest('created_at')
        self.assertEqual(order.payment_method, 'online')
        self.assertEqual(order.payment_status, 'pending')
        self.assertIsNotNone(order.paymongo_session_id)

    def test_payment_success_callback_verifies_payment(self):
        """Verify that payment_success view retrieves checkout session, updates payment status to paid."""
        order = Order.objects.create(
            product=self.product,
            full_name='Samantha P.',
            phone_number='09171234567',
            shipping_address='Cebu City',
            payment_method='online',
            payment_status='pending',
            paymongo_session_id='pm_mock_sess_99_12345'
        )
        
        response = self.client.get(reverse('store:payment_success'), {'session_id': 'pm_mock_sess_99_12345'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thank You For Your Payment!")
        self.assertContains(response, "#KELS-ORDER-")
        
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'paid')
        self.assertIsNotNone(order.paymongo_payment_intent_id)

    def test_payment_success_callback_invalid_session(self):
        """Verify callback handles invalid sessions gracefully by redirecting to shop."""
        response = self.client.get(reverse('store:payment_success'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('store:store_catalog'))


from django.core.cache import cache
from django.test import override_settings
import json

@override_settings(PAYMONGO_SECRET_KEY='pm_mock_secret_key', PAYMONGO_WEBHOOK_SECRET='')
class StorePhase3AutomationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            title="Premium Gaming Mouse",
            price=1899.00,
            sku="AG-MAX-PRO-01",
            cj_product_id="cj_prod_id_abc123",
            is_active=True
        )
        cache.clear()

    @override_settings(CJ_USE_SANDBOX=True)
    def test_paymongo_webhook_paid_event(self):
        """Verify that PayMongo webhook for checkout session paid updates order & dispatches to CJ."""
        order = Order.objects.create(
            product=self.product,
            full_name='Juan Dela Cruz',
            phone_number='09176543210',
            shipping_address='Manila',
            payment_method='online',
            payment_status='pending',
            paymongo_session_id='cs_session_xyz123'
        )

        webhook_payload = {
            "data": {
                "attributes": {
                    "type": "checkout_session.payment.paid",
                    "data": {
                        "id": "cs_session_xyz123",
                        "attributes": {
                            "status": "payment_success",
                            "payments": [
                                {
                                    "id": "pay_intent_9988",
                                    "attributes": {
                                        "status": "paid"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }

        response = self.client.post(
            reverse('store:paymongo_webhook'),
            data=json.dumps(webhook_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")

        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'paid')
        self.assertEqual(order.paymongo_payment_intent_id, 'pay_intent_9988')
        
        # In mock sandbox mode, this should have automatically fulfilled the order
        self.assertEqual(order.fulfillment_status, 'fulfilled')
        self.assertIsNotNone(order.cj_order_id)

    @override_settings(CJ_USE_SANDBOX=True, CJ_AUTO_FULFILL_COD=True)
    def test_auto_fulfillment_cod_enabled(self):
        """Verify that when CJ_AUTO_FULFILL_COD is True, checkout dispatches COD instantly to CJ."""
        post_data = {
            'full_name': 'Maria Clara',
            'phone_number': '09181112233',
            'shipping_address': 'Vigan, Ilocos Sur',
            'payment_method': 'cod'
        }
        response = self.client.post(reverse('store:landing_page'), post_data)
        self.assertEqual(response.status_code, 200)
        
        order = Order.objects.latest('created_at')
        self.assertEqual(order.fulfillment_status, 'fulfilled')
        self.assertIsNotNone(order.cj_order_id)

    @override_settings(CJ_USE_SANDBOX=True, CJ_AUTO_FULFILL_COD=False)
    def test_auto_fulfillment_cod_disabled(self):
        """Verify that when CJ_AUTO_FULFILL_COD is False, checkout does NOT dispatch COD automatically."""
        post_data = {
            'full_name': 'Maria Clara',
            'phone_number': '09181112233',
            'shipping_address': 'Vigan, Ilocos Sur',
            'payment_method': 'cod'
        }
        response = self.client.post(reverse('store:landing_page'), post_data)
        self.assertEqual(response.status_code, 200)
        
        order = Order.objects.latest('created_at')
        self.assertEqual(order.fulfillment_status, 'pending')
        self.assertIsNone(order.cj_order_id)

    @override_settings(CJ_USE_SANDBOX=True)
    def test_product_stock_api_caching(self):
        """Verify product stock API returns count and correctly caches the value."""
        # Clean cache
        cache_key = f"cj_stock_{self.product.sku}"
        self.assertIsNone(cache.get(cache_key))

        # First request (queries CJ - mocked)
        response1 = self.client.get(reverse('store:product_stock_api', args=[self.product.slug]))
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        self.assertTrue(data1['success'])
        stock_val = data1['stock']
        self.assertGreaterEqual(stock_val, 0)

        # Check cache was populated
        self.assertEqual(cache.get(cache_key), stock_val)

        # Modify product stock directly in cache to verify cache hits
        cache.set(cache_key, 9999, 600)
        
        # Second request (must be a cache hit)
        response2 = self.client.get(reverse('store:product_stock_api', args=[self.product.slug]))
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(data2['stock'], 9999)



