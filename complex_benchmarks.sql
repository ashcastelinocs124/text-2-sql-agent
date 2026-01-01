-- Gold Queries for SQL Agent Testing
-- Complex SQL queries with various difficulty levels

-- Query 1: Simple SELECT with WHERE (Easy)
-- Find all customers from New York
SELECT customer_id, first_name, last_name, city, state 
FROM customers 
WHERE city = 'New York' 
ORDER BY last_name, first_name;

-- Query 2: JOIN with aggregation (Medium)
-- Show total revenue per customer with their names
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    COUNT(o.order_id) as order_count,
    COALESCE(SUM(o.total_amount), 0) as total_revenue
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_status != 'cancelled' OR o.order_id IS NULL
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_revenue DESC;

-- Query 3: Complex multi-table JOIN (Hard)
-- Find top 5 products with highest revenue including category and supplier info
SELECT 
    p.product_name,
    c.category_name,
    s.supplier_name,
    SUM(oi.quantity * oi.total_price) as total_revenue,
    SUM(oi.quantity) as total_sold
FROM products p
JOIN categories c ON p.category_id = c.category_id
JOIN suppliers s ON p.supplier_id = s.supplier_id
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status != 'cancelled'
GROUP BY p.product_id, p.product_name, c.category_name, s.supplier_name
ORDER BY total_revenue DESC
LIMIT 5;

-- Query 4: Subquery with EXISTS (Hard)
-- Find customers who have purchased products with ratings above 4.5
SELECT DISTINCT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email
FROM customers c
WHERE EXISTS (
    SELECT 1
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.customer_id = c.customer_id
    AND o.order_status != 'cancelled'
    AND p.rating > 4.5
)
ORDER BY c.last_name, c.first_name;

-- Query 5: Window function query (Enterprise)
-- Rank customers by total spending and show their spending percentile
SELECT 
    customer_id,
    first_name,
    last_name,
    total_spent,
    RANK() OVER (ORDER BY total_spent DESC) as spending_rank,
    PERCENT_RANK() OVER (ORDER BY total_spent DESC) as spending_percentile
FROM (
    SELECT 
        c.customer_id,
        c.first_name,
        c.last_name,
        COALESCE(SUM(o.total_amount), 0) as total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status != 'cancelled' OR o.order_id IS NULL
    GROUP BY c.customer_id, c.first_name, c.last_name
) customer_spending
ORDER BY spending_rank;

-- Query 6: CTE (Common Table Expression) (Enterprise)
-- Find customers whose order value is above average using CTE
WITH customer_order_stats AS (
    SELECT 
        c.customer_id,
        c.first_name,
        c.last_name,
        COUNT(o.order_id) as order_count,
        COALESCE(AVG(o.total_amount), 0) as avg_order_value,
        COALESCE(SUM(o.total_amount), 0) as total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status != 'cancelled' OR o.order_id IS NULL
    GROUP BY c.customer_id, c.first_name, c.last_name
),
overall_avg AS (
    SELECT AVG(avg_order_value) as overall_avg_order_value
    FROM customer_order_stats
    WHERE order_count > 0
)
SELECT 
    cos.customer_id,
    cos.first_name,
    cos.last_name,
    cos.order_count,
    cos.avg_order_value,
    cos.total_spent,
    oa.overall_avg_order_value,
    (cos.avg_order_value - oa.overall_avg_order_value) as difference_from_avg
FROM customer_order_stats cos
CROSS JOIN overall_avg oa
WHERE cos.order_count > 0
AND cos.avg_order_value > oa.overall_avg_order_value
ORDER BY cos.avg_order_value DESC;

-- Query 7: Date-based analysis (Medium)
-- Show monthly revenue trends for current year
SELECT 
    DATE_TRUNC('month', order_date) as month,
    COUNT(order_id) as order_count,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_order_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM orders
WHERE order_status != 'cancelled'
AND order_date >= DATE_TRUNC('year', CURRENT_DATE)
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month;

-- Query 8: Product performance analysis (Hard)
-- Analyze product performance with review correlation
SELECT 
    p.product_id,
    p.product_name,
    c.category_name,
    p.unit_price,
    p.rating,
    p.review_count,
    COALESCE(sales.total_sold, 0) as units_sold,
    COALESCE(sales.total_revenue, 0) as revenue,
    CASE 
        WHEN p.review_count > 0 THEN 
            CASE WHEN sales.total_sold > 0 THEN sales.total_sold::FLOAT / p.review_count ELSE 0 END
        ELSE 0 
    END as sales_per_review
FROM products p
JOIN categories c ON p.category_id = c.category_id
LEFT JOIN (
    SELECT 
        oi.product_id,
        SUM(oi.quantity) as total_sold,
        SUM(oi.total_price) as total_revenue
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status != 'cancelled'
    GROUP BY oi.product_id
) sales ON p.product_id = sales.product_id
WHERE p.is_active = true
ORDER BY revenue DESC NULLS LAST
LIMIT 20;

-- Query 9: Customer segmentation analysis (Hard)
-- Analyze customer segments with their actual spending patterns
SELECT 
    cs.segment_name,
    COUNT(c.customer_id) as customer_count,
    COALESCE(AVG(order_stats.avg_order_value), 0) as avg_order_value,
    COALESCE(SUM(order_stats.total_spent), 0) as segment_revenue,
    COALESCE(AVG(order_stats.order_count), 0) as avg_orders_per_customer,
    cs.min_total_spent as expected_min_spent,
    cs.max_total_spent as expected_max_spent
FROM customer_segments cs
LEFT JOIN customers c ON cs.segment_id = c.customer_segment_id
LEFT JOIN (
    SELECT 
        c.customer_id,
        c.customer_segment_id,
        COUNT(o.order_id) as order_count,
        COALESCE(AVG(o.total_amount), 0) as avg_order_value,
        COALESCE(SUM(o.total_amount), 0) as total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status != 'cancelled' OR o.order_id IS NULL
    GROUP BY c.customer_id, c.customer_segment_id
) order_stats ON c.customer_id = order_stats.customer_id
GROUP BY cs.segment_id, cs.segment_name, cs.min_total_spent, cs.max_total_spent
ORDER BY segment_revenue DESC;

-- Query 10: Complex conditional aggregation (Hard)
-- Show order status breakdown by payment method with conditional totals
SELECT 
    payment_method,
    COUNT(*) as total_orders,
    COUNT(CASE WHEN order_status = 'delivered' THEN 1 END) as delivered_orders,
    COUNT(CASE WHEN order_status = 'cancelled' THEN 1 END) as cancelled_orders,
    COUNT(CASE WHEN order_status = 'pending' THEN 1 END) as pending_orders,
    SUM(CASE WHEN order_status != 'cancelled' THEN total_amount ELSE 0 END) as successful_revenue,
    SUM(CASE WHEN order_status = 'cancelled' THEN total_amount ELSE 0 END) as cancelled_revenue,
    AVG(CASE WHEN order_status != 'cancelled' THEN total_amount ELSE NULL END) as avg_successful_order,
    ROUND(
        COUNT(CASE WHEN order_status = 'delivered' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 2
    ) as delivery_rate_percent
FROM orders
GROUP BY payment_method
ORDER BY successful_revenue DESC;

-- Query 11: Supplier performance analysis (Enterprise)
-- Rank suppliers by product performance and customer satisfaction
SELECT 
    s.supplier_id,
    s.supplier_name,
    s.country,
    s.rating as supplier_rating,
    COUNT(DISTINCT p.product_id) as product_count,
    COALESCE(AVG(p.rating), 0) as avg_product_rating,
    COALESCE(SUM(sales.total_revenue), 0) as total_revenue,
    COALESCE(SUM(sales.units_sold), 0) as total_units_sold,
    RANK() OVER (ORDER BY COALESCE(SUM(sales.total_revenue), 0) DESC) as revenue_rank
FROM suppliers s
LEFT JOIN products p ON s.supplier_id = p.supplier_id
LEFT JOIN (
    SELECT 
        oi.product_id,
        SUM(oi.quantity) as units_sold,
        SUM(oi.total_price) as total_revenue
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status != 'cancelled'
    GROUP BY oi.product_id
) sales ON p.product_id = sales.product_id
GROUP BY s.supplier_id, s.supplier_name, s.country, s.rating
ORDER BY total_revenue DESC NULLS LAST;

-- Query 12: Time-based cohort analysis (Enterprise)
-- Customer cohort analysis by registration month
WITH customer_cohorts AS (
    SELECT 
        customer_id,
        DATE_TRUNC('month', registration_date) as cohort_month
    FROM customers
),
cohort_orders AS (
    SELECT 
        cc.cohort_month,
        o.customer_id,
        DATE_TRUNC('month', o.order_date) as order_month,
        o.order_id,
        o.total_amount
    FROM customer_cohorts cc
    JOIN orders o ON cc.customer_id = o.customer_id
    WHERE o.order_status != 'cancelled'
),
cohort_summary AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_id) as cohort_size,
        COUNT(DISTINCT order_id) as total_orders,
        SUM(total_amount) as total_revenue,
        AVG(total_amount) as avg_order_value
    FROM cohort_orders
    GROUP BY cohort_month
)
SELECT 
    cohort_month,
    cohort_size,
    total_orders,
    ROUND(total_orders::FLOAT / NULLIF(cohort_size, 0), 2) as orders_per_customer,
    total_revenue,
    avg_order_value,
    ROUND(total_revenue::FLOAT / NULLIF(cohort_size, 0), 2) as revenue_per_customer
FROM cohort_summary
ORDER BY cohort_month;
