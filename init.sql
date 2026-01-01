-- Initialize test database with sample tables

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    category VARCHAR(100)
);

-- Insert sample data
INSERT INTO users (name, email, age) VALUES
    ('Alice Johnson', 'alice@example.com', 28),
    ('Bob Smith', 'bob@example.com', 35),
    ('Charlie Brown', 'charlie@example.com', 42),
    ('Diana Prince', 'diana@example.com', 31);

INSERT INTO products (name, price, stock, category) VALUES
    ('Laptop', 999.99, 50, 'Electronics'),
    ('Mouse', 29.99, 200, 'Electronics'),
    ('Desk Chair', 199.99, 30, 'Furniture'),
    ('Monitor', 299.99, 75, 'Electronics'),
    ('Keyboard', 79.99, 150, 'Electronics');

INSERT INTO orders (user_id, amount, status) VALUES
    (1, 999.99, 'completed'),
    (1, 29.99, 'completed'),
    (2, 199.99, 'pending'),
    (3, 299.99, 'completed'),
    (4, 79.99, 'shipped');
