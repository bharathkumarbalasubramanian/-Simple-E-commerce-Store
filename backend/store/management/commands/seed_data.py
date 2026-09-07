from django.core.management.base import BaseCommand
from store.models import Category, Product

class Command(BaseCommand):
    help = 'Seeds initial sample categories and products for testing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding database with sample products...'))

        categories_data = [
            {'name': 'Audio & Headphones', 'description': 'Premium noise-canceling headphones, earbuds, and hi-fi audio accessories.'},
            {'name': 'Wearables & Watches', 'description': 'Smartwatches, fitness trackers, and modern wristwear accessories.'},
            {'name': 'Laptops & Computers', 'description': 'High-performance laptops, monitors, mechanical keyboards, and workspace gear.'},
            {'name': 'Smart Home', 'description': 'Smart ambient lighting, connected speakers, and modern IoT household gadgets.'},
        ]

        cat_objs = {}
        for cat_info in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=cat_info['name'],
                defaults={'description': cat_info['description']}
            )
            cat_objs[cat.name] = cat

        products_data = [
            {
                'category': cat_objs['Audio & Headphones'],
                'name': 'Aura Noise-Canceling Wireless Headphones',
                'description': 'Experience studio-grade active noise cancellation with 40-hour battery life, plush memory foam earcups, and crystal-clear acoustic drivers.',
                'price': 249.99,
                'stock': 15,
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['Audio & Headphones'],
                'name': 'Pulse Pro True Wireless Earbuds',
                'description': 'Compact spatial audio earbuds featuring ergonomic fit, IPX7 water resistance, wireless charging case, and ambient transparency mode.',
                'price': 129.50,
                'stock': 25,
                'image_url': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['Wearables & Watches'],
                'name': 'Apex Smartwatch Ultra',
                'description': 'High-precision GPS smartwatch with sapphire crystal display, titanium bezel, heart-rate monitoring, and 7-day battery life.',
                'price': 399.00,
                'stock': 10,
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['Laptops & Computers'],
                'name': 'Vortex M1 Minimal Mechanical Keyboard',
                'description': 'Low-profile wireless mechanical keyboard with hot-swappable tactile switches, RGB backlighting, and CNC aluminum casing.',
                'price': 149.99,
                'stock': 18,
                'image_url': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['Laptops & Computers'],
                'name': 'ErgoStream Precision Wireless Mouse',
                'description': 'Ergonomic multi-device wireless mouse with hyperspeed scrolling, custom macro buttons, and silent click feedback.',
                'price': 79.95,
                'stock': 30,
                'image_url': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['Smart Home'],
                'name': 'GlowSync RGB Smart Desk Lamp',
                'description': 'Adjustable color-temperature desk lamp with wireless smartphone charging pad, ambient mood light sync, and touch bar controls.',
                'price': 89.99,
                'stock': 20,
                'image_url': 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['Audio & Headphones'],
                'name': 'HiFi Studio Desktop Speakers',
                'description': 'Hand-crafted wooden cabinet bookshelf speakers with bluetooth 5.2 connectivity, rich bass reflex ports, and dedicated remote.',
                'price': 199.99,
                'stock': 8,
                'image_url': 'https://images.unsplash.com/photo-1545454675-3531b543be5d?w=800&auto=format&fit=crop&q=80',
            },
            {
                'category': cat_objs['Laptops & Computers'],
                'name': 'UltraView 4K Curved Monitor Stand',
                'description': 'Minimalist aluminum laptop & monitor stand with built-in USB-C hub and cable management channel.',
                'price': 64.50,
                'stock': 12,
                'image_url': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800&auto=format&fit=crop&q=80',
            },
        ]

        created_count = 0
        for p_info in products_data:
            p, created = Product.objects.get_or_create(
                name=p_info['name'],
                defaults={
                    'category': p_info['category'],
                    'description': p_info['description'],
                    'price': p_info['price'],
                    'stock': p_info['stock'],
                    'image_url': p_info['image_url'],
                    'is_available': True
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} sample products!'))
