#!/usr/bin/env python3
"""
Complex Sample Data Generator for SQL Agent Testing
Creates realistic e-commerce data with complex relationships
"""

import random
import json
from datetime import datetime, timedelta
from decimal import Decimal
import psycopg2
from psycopg2.extras import execute_values

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'testdb',
    'user': 'testuser',
    'password': 'testpass'
}

# Sample data generators
FIRST_NAMES = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 
               'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
               'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
               'Matthew', 'Betty', 'Anthony', 'Helen', 'Mark', 'Sandra', 'Donald', 'Donna']

LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
              'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
              'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White',
              'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King']

CITIES = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio',
          'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville', 'Fort Worth', 'Columbus',
          'Charlotte', 'San Francisco', 'Indianapolis', 'Seattle', 'Denver', 'Washington']

STATES = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'FL', 'OH', 'NC', 'GA', 'MI', 'WA', 'CO', 'VA', 'OR']

COUNTRIES = ['USA', 'Canada', 'UK', 'Germany', 'France', 'Australia', 'Japan', 'China', 'India', 'Brazil']

PRODUCT_NAMES = [
    'Wireless Bluetooth Headphones', 'Smart Watch Series 5', 'Laptop Stand Adjustable', 
    'USB-C Hub 7-in-1', 'Mechanical Keyboard RGB', 'Wireless Mouse Ergonomic',
    '4K Webcam Pro', 'Monitor 27-inch 4K', 'Desk Lamp LED', 'Phone Case Premium',
    'Tablet 10-inch', 'External SSD 1TB', 'Graphics Card RTX', 'Power Supply 750W',
    'CPU Cooler Liquid', 'Motherboard Gaming', 'RAM 16GB DDR4', 'Case ATX Mid Tower',
    'Cable Management Kit', 'Mouse Pad XXL'
]

CATEGORIES = [
    ('Electronics', None, 1),
    ('Computers', 'Electronics', 2),
    ('Audio', 'Electronics', 2),
    ('Mobile', 'Electronics', 2),
    ('Accessories', 'Electronics', 2),
    ('Computer Components', 'Computers', 3),
    ('Peripherals', 'Computers', 3),
    ('Laptops', 'Computers', 3),
    ('Headphones', 'Audio', 3),
    ('Speakers', 'Audio', 3),
    ('Phone Accessories', 'Mobile', 3),
    ('Tablets', 'Mobile', 3)
]

SUPPLIERS = [
    ('TechSupply Pro', 'contact@techsupply.com', '555-0101', 'USA', 4.5, 15),
    ('Global Components Inc', 'sales@globalcomp.com', '555-0102', 'China', 4.2, 20),
    ('EuroTech Solutions', 'info@eurotech.com', '555-0103', 'Germany', 4.7, 12),
    ('AsiaDirect Trading', 'orders@asiadirect.com', '555-0104', 'Japan', 4.3, 18),
    ('LocalParts Co', 'hello@localparts.com', '555-0105', 'USA', 4.8, 8)
]

class DataGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        
    def generate_customer_segments(self):
        segments = [
            ('Bronze', 'Entry-level customers with 1-5 purchases', 1, 5, 0, 500),
            ('Silver', 'Regular customers with 6-20 purchases', 6, 20, 500, 2000),
            ('Gold', 'Premium customers with 21-50 purchases', 21, 50, 2000, 5000),
            ('Platinum', 'VIP customers with 50+ purchases', 50, 999, 5000, 99999)
        ]
        
        for seg in segments:
            self.cursor.execute("""
                INSERT INTO customer_segments (segment_name, description, min_purchase_count, 
                                             max_purchase_count, min_total_spent, max_total_spent)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, seg)
        
        print(f"Generated {len(segments)} customer segments")
    
    def generate_categories(self):
        # First insert root categories
        root_categories = [cat for cat in CATEGORIES if cat[1] is None]
        for cat in root_categories:
            category_name, parent_category_id, level = cat
            description = f"{category_name} category"
            self.cursor.execute("""
                INSERT INTO categories (category_name, parent_category_id, level, description)
                VALUES (%s, %s, %s, %s)
            """, (category_name, parent_category_id, level, description))
        
        # Then insert child categories with proper parent IDs
        self.conn.commit()
        
        # Get mapping of category names to IDs
        self.cursor.execute("SELECT category_id, category_name FROM categories")
        category_map = {row[1]: row[0] for row in self.cursor.fetchall()}
        
        child_categories = [cat for cat in CATEGORIES if cat[1] is not None]
        for cat in child_categories:
            category_name, parent_name, level = cat
            parent_id = category_map.get(parent_name)
            description = f"{category_name} category"
            self.cursor.execute("""
                INSERT INTO categories (category_name, parent_category_id, level, description)
                VALUES (%s, %s, %s, %s)
            """, (category_name, parent_id, level, description))
        
        print(f"Generated {len(CATEGORIES)} categories")
    
    def generate_suppliers(self):
        for sup in SUPPLIERS:
            self.cursor.execute("""
                INSERT INTO suppliers (supplier_name, contact_email, phone, country, rating, years_in_business)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, sup)
        
        print(f"Generated {len(SUPPLIERS)} suppliers")
    
    def generate_customers(self, count=200):
        customers = []
        for i in range(count):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
            
            # Random registration date in last 2 years
            reg_date = datetime.now() - timedelta(days=random.randint(1, 730))
            dob = reg_date - timedelta(days=random.randint(18*365, 65*365))
            
            city = random.choice(CITIES)
            state = random.choice(STATES)
            country = random.choice(COUNTRIES)
            zip_code = f"{random.randint(10000, 99999)}"
            
            # Assign segment based on random logic
            segment_id = random.randint(1, 4)
            loyalty_points = random.randint(0, 5000)
            
            customers.append((
                first_name, last_name, email, f"555-{random.randint(1000, 9999)}",
                dob.date(), reg_date.date(), city, state, country, zip_code,
                segment_id, loyalty_points, 'active'
            ))
        
        execute_values(self.cursor, """
            INSERT INTO customers (first_name, last_name, email, phone, date_of_birth,
                                 registration_date, city, state, country, zip_code,
                                 customer_segment_id, loyalty_points, account_status)
            VALUES %s
        """, customers)
        
        print(f"Generated {count} customers")
    
    def generate_products(self, count=100):
        products = []
        used_skus = set()
        for i in range(count):
            name = random.choice(PRODUCT_NAMES) + f" {i+1}"
            # Ensure unique SKU
            while True:
                sku = f"SKU-{random.randint(10000, 99999)}"
                if sku not in used_skus:
                    used_skus.add(sku)
                    break
            category_id = random.randint(1, len(CATEGORIES))
            supplier_id = random.randint(1, len(SUPPLIERS))
            
            unit_price = round(random.uniform(9.99, 999.99), 2)
            cost_price = round(unit_price * random.uniform(0.6, 0.8), 2)
            weight = round(random.uniform(0.1, 5.0), 3)
            stock = random.randint(0, 500)
            reorder_level = random.randint(5, 20)
            
            date_added = datetime.now() - timedelta(days=random.randint(1, 365))
            
            # Some products are discontinued
            is_active = random.random() > 0.1
            date_discontinued = None
            if not is_active:
                date_discontinued = date_added + timedelta(days=random.randint(30, 200))
            
            rating = round(random.uniform(3.0, 5.0), 1)
            review_count = random.randint(0, 500)
            
            products.append((
                name, sku, category_id, supplier_id, f"High quality {name.lower()}",
                unit_price, cost_price, weight, stock, reorder_level, date_added.date(),
                date_discontinued, is_active, rating, review_count
            ))
        
        execute_values(self.cursor, """
            INSERT INTO products (product_name, sku, category_id, supplier_id, description,
                                 unit_price, cost_price, weight_kg, stock_quantity, reorder_level,
                                 date_added, date_discontinued, is_active, rating, review_count)
            VALUES %s
        """, products)
        
        print(f"Generated {count} products")
    
    def generate_product_reviews(self, count=500):
        reviews = []
        for i in range(count):
            product_id = random.randint(1, 100)
            customer_id = random.randint(1, 200)
            rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 30, 35])[0]
            
            review_texts = [
                "Great product, highly recommended!",
                "Good value for money.",
                "Average quality, meets expectations.",
                "Not what I expected, disappointing.",
                "Excellent! Exceeded all expectations.",
                "Poor quality, would not buy again.",
                "Decent product, room for improvement.",
                "Outstanding quality and service."
            ]
            
            review_text = random.choice(review_texts)
            review_date = datetime.now() - timedelta(days=random.randint(1, 365))
            helpful_count = random.randint(0, 50)
            verified = random.random() > 0.3
            
            reviews.append((
                product_id, customer_id, rating, review_text, review_date.date(),
                helpful_count, verified
            ))
        
        execute_values(self.cursor, """
            INSERT INTO product_reviews (product_id, customer_id, rating, review_text,
                                         review_date, helpful_count, verified_purchase)
            VALUES %s
        """, reviews)
        
        print(f"Generated {count} product reviews")
    
    def generate_orders(self, count=300):
        orders = []
        for i in range(count):
            customer_id = random.randint(1, 200)
            order_date = datetime.now() - timedelta(days=random.randint(1, 365),
                                                     hours=random.randint(0, 23),
                                                     minutes=random.randint(0, 59))
            
            statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
            order_status = random.choices(statuses, weights=[10, 20, 30, 35, 5])[0]
            
            payment_methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer', 'crypto']
            payment_method = random.choice(payment_methods)
            
            payment_statuses = ['pending', 'completed', 'failed', 'refunded']
            payment_status = random.choices(payment_statuses, weights=[10, 70, 15, 5])[0]
            
            # Generate realistic addresses
            shipping_address = f"{random.randint(100, 999)} {random.choice(['Main', 'Oak', 'Pine', 'Elm', 'Maple'])} St, {random.choice(CITIES)}, {random.choice(STATES)} {random.randint(10000, 99999)}"
            billing_address = shipping_address  # Same as shipping for simplicity
            
            # Calculate order totals
            num_items = random.randint(1, 5)
            subtotal = round(random.uniform(50.0, 500.0), 2)
            tax_amount = round(subtotal * 0.08, 2)
            shipping_cost = round(random.uniform(0.0, 25.0), 2)
            discount_amount = round(random.uniform(0.0, 50.0), 2)
            total_amount = subtotal + tax_amount + shipping_cost - discount_amount
            
            promo_code = None
            if discount_amount > 0:
                promo_codes = ['SAVE10', 'WELCOME20', 'SPECIAL30', 'HOLIDAY15']
                promo_code = random.choice(promo_codes)
            
            orders.append((
                customer_id, order_date, order_status, payment_method, payment_status,
                shipping_address, billing_address, subtotal, tax_amount, shipping_cost,
                discount_amount, total_amount, 'USD', promo_code
            ))
        
        execute_values(self.cursor, """
            INSERT INTO orders (customer_id, order_date, order_status, payment_method,
                              payment_status, shipping_address, billing_address, subtotal,
                              tax_amount, shipping_cost, discount_amount, total_amount,
                              currency, promo_code)
            VALUES %s
        """, orders)
        
        print(f"Generated {count} orders")
    
    def generate_order_items(self, avg_items_per_order=3):
        order_items = []
        
        self.cursor.execute("SELECT MAX(order_id) FROM orders")
        max_order_id = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT MAX(product_id) FROM products")
        max_product_id = self.cursor.fetchone()[0]
        
        for order_id in range(1, max_order_id + 1):
            num_items = random.randint(1, avg_items_per_order + 2)
            
            for _ in range(num_items):
                product_id = random.randint(1, max_product_id)
                quantity = random.randint(1, 5)
                
                # Get product price
                self.cursor.execute("SELECT unit_price FROM products WHERE product_id = %s", (product_id,))
                unit_price = float(self.cursor.fetchone()[0])
                
                discount_percent = random.uniform(0, 20)
                total_price = round(quantity * unit_price * (1 - discount_percent/100), 2)
                
                item_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
                item_status = random.choices(item_statuses, weights=[10, 20, 30, 35, 5])[0]
                
                order_items.append((
                    order_id, product_id, quantity, unit_price, discount_percent,
                    total_price, item_status
                ))
        
        execute_values(self.cursor, """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price,
                                    discount_percent, total_price, item_status)
            VALUES %s
        """, order_items)
        
        print(f"Generated {len(order_items)} order items")
    
    def generate_all(self):
        print("Starting complex data generation...")
        
        try:
            self.generate_customer_segments()
            self.conn.commit()
            
            self.generate_categories()
            self.conn.commit()
            
            self.generate_suppliers()
            self.conn.commit()
            
            self.generate_customers(200)
            self.conn.commit()
            
            self.generate_products(100)
            self.conn.commit()
            
            self.generate_product_reviews(500)
            self.conn.commit()
            
            self.generate_orders(300)
            self.conn.commit()
            
            self.generate_order_items(3)
            self.conn.commit()
            
            print("✅ All complex data generated successfully!")
            
            # Print summary statistics
            self.print_statistics()
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error generating data: {e}")
            raise
        finally:
            self.cursor.close()
            self.conn.close()
    
    def print_statistics(self):
        stats = [
            ("Customers", "SELECT COUNT(*) FROM customers"),
            ("Products", "SELECT COUNT(*) FROM products"),
            ("Orders", "SELECT COUNT(*) FROM orders"),
            ("Order Items", "SELECT COUNT(*) FROM order_items"),
            ("Product Reviews", "SELECT COUNT(*) FROM product_reviews"),
            ("Categories", "SELECT COUNT(*) FROM categories"),
            ("Suppliers", "SELECT COUNT(*) FROM suppliers"),
            ("Customer Segments", "SELECT COUNT(*) FROM customer_segments"),
            ("Total Revenue", "SELECT SUM(total_amount) FROM orders WHERE order_status != 'cancelled'"),
            ("Avg Order Value", "SELECT AVG(total_amount) FROM orders WHERE order_status != 'cancelled'"),
            ("Products with Reviews", "SELECT COUNT(DISTINCT product_id) FROM product_reviews"),
            ("Avg Product Rating", "SELECT AVG(rating) FROM product_reviews")
        ]
        
        print("\n📊 Database Statistics:")
        print("=" * 40)
        
        for label, query in stats:
            try:
                self.cursor.execute(query)
                result = self.cursor.fetchone()[0]
                if isinstance(result, float):
                    print(f"{label:25}: {result:.2f}")
                else:
                    print(f"{label:25}: {result}")
            except Exception as e:
                print(f"{label:25}: Error - {e}")

if __name__ == "__main__":
    generator = DataGenerator()
    generator.generate_all()
