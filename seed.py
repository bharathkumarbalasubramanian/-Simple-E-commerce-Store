from database import engine, Base, SessionLocal
import models
from auth import get_password_hash

def seed_db():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Create default admin user if not existing
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            admin_user = models.User(
                username="admin",
                email="admin@codealpha.com",
                hashed_password=get_password_hash("admin123"),
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created: admin / admin123")

        # Seed categories & products if none exist
        if db.query(models.Category).count() == 0:
            categories_data = [
                {'name': 'Audio & Headphones', 'slug': 'audio-headphones', 'description': 'Premium noise-canceling headphones, earbuds, and hi-fi audio accessories.'},
                {'name': 'Wearables & Watches', 'slug': 'wearables-watches', 'description': 'Smartwatches, fitness trackers, and modern wristwear accessories.'},
                {'name': 'Laptops & Computers', 'slug': 'laptops-computers', 'description': 'High-performance laptops, monitors, mechanical keyboards, and workspace gear.'},
                {'name': 'Smart Home', 'slug': 'smart-home', 'description': 'Smart ambient lighting, connected speakers, and modern IoT household gadgets.'},
            ]

            cat_objs = {}
            for cat_info in categories_data:
                cat = models.Category(name=cat_info['name'], slug=cat_info['slug'], description=cat_info['description'])
                db.add(cat)
                db.flush()
                cat_objs[cat.name] = cat

            products_data = [
                {
                    'category': cat_objs['Audio & Headphones'],
                    'name': 'Aura Noise-Canceling Wireless Headphones',
                    'slug': 'aura-noise-canceling-wireless-headphones',
                    'description': 'Experience studio-grade active noise cancellation with 40-hour battery life, plush memory foam earcups, and crystal-clear acoustic drivers.',
                    'price': 249.99,
                    'stock': 15,
                    'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80',
                },
                {
                    'category': cat_objs['Audio & Headphones'],
                    'name': 'Pulse Pro True Wireless Earbuds',
                    'slug': 'pulse-pro-true-wireless-earbuds',
                    'description': 'Compact spatial audio earbuds featuring ergonomic fit, IPX7 water resistance, wireless charging case, and ambient transparency mode.',
                    'price': 129.50,
                    'stock': 25,
                    'image_url': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800&auto=format&fit=crop&q=80',
                },
                {
                    'category': cat_objs['Wearables & Watches'],
                    'name': 'Apex Smartwatch Ultra',
                    'slug': 'apex-smartwatch-ultra',
                    'description': 'High-precision GPS smartwatch with sapphire crystal display, titanium bezel, heart-rate monitoring, and 7-day battery life.',
                    'price': 399.00,
                    'stock': 10,
                    'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=80',
                },
                {
                    'category': cat_objs['Laptops & Computers'],
                    'name': 'Vortex M1 Minimal Mechanical Keyboard',
                    'slug': 'vortex-m1-minimal-mechanical-keyboard',
                    'description': 'Low-profile wireless mechanical keyboard with hot-swappable tactile switches, RGB backlighting, and CNC aluminum casing.',
                    'price': 149.99,
                    'stock': 18,
                    'image_url': 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800&auto=format&fit=crop&q=80',
                },
                {
                    'category': cat_objs['Laptops & Computers'],
                    'name': 'ErgoStream Precision Wireless Mouse',
                    'slug': 'ergostream-precision-wireless-mouse',
                    'description': 'Ergonomic multi-device wireless mouse with hyperspeed scrolling, custom macro buttons, and silent click feedback.',
                    'price': 79.95,
                    'stock': 30,
                    'image_url': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800&auto=format&fit=crop&q=80',
                },
                {
                    'category': cat_objs['Smart Home'],
                    'name': 'GlowSync RGB Smart Desk Lamp',
                    'slug': 'glowsync-rgb-smart-desk-lamp',
                    'description': 'Adjustable color-temperature desk lamp with wireless smartphone charging pad, ambient mood light sync, and touch bar controls.',
                    'price': 89.99,
                    'stock': 20,
                    'image_url': 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&auto=format&fit=crop&q=80',
                },
            ]

            for p_info in products_data:
                prod = models.Product(
                    category_id=p_info['category'].id,
                    name=p_info['name'],
                    slug=p_info['slug'],
                    description=p_info['description'],
                    price=p_info['price'],
                    stock=p_info['stock'],
                    image_url=p_info['image_url'],
                    is_available=True
                )
                db.add(prod)

            db.commit()
            print("Successfully seeded categories and products!")
        else:
            print("Products already seeded.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
