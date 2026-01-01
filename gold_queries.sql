-- GOLD STANDARD QUERY 1
-- Description: Find High Value Customers (spent > $100) and rank them.
-- Efficiency: Uses CTE to aggregate first, reducing main query complexity.
WITH UserSpending AS (
    SELECT 
        u.id,
        u.name,
        COUNT(o.id) as order_count,
        COALESCE(SUM(o.amount), 0) as total_spent
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    GROUP BY u.id, u.name
)
SELECT 
    name,
    order_count,
    ROUND(total_spent, 2) as total_spent,
    DENSE_RANK() OVER (ORDER BY total_spent DESC) as spending_rank
FROM UserSpending
WHERE total_spent > 100
ORDER BY spending_rank;

-- GOLD STANDARD QUERY 2
-- Description: Pivot table summary of Order Statuses per user.
-- Efficiency: Uses conditional aggregation (CASE WHEN) to pivot in a single pass.
SELECT 
    u.name,
    COUNT(CASE WHEN o.status = 'completed' THEN 1 END) as completed_orders,
    COUNT(CASE WHEN o.status = 'pending' THEN 1 END) as pending_orders,
    COUNT(CASE WHEN o.status = 'shipped' THEN 1 END) as shipped_orders,
    COUNT(CASE WHEN o.status IN ('cancelled', 'refunded') THEN 1 END) as failed_orders,
    ROUND(AVG(o.amount), 2) as avg_order_value
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY u.name
HAVING COUNT(o.id) > 0
ORDER BY u.name;

-- GOLD STANDARD QUERY 3
-- Description: Find products cheaper than a user's average spend (Cross-sell potential).
-- Efficiency: Uses explicit CROSS JOIN and pre-calculated averages.
SELECT 
    u.name as user_name,
    p.name as affordable_product,
    p.price,
    ROUND(AVG(o.amount), 2) as user_avg_spend
FROM users u
JOIN orders o ON u.id = o.user_id
CROSS JOIN products p
GROUP BY u.id, u.name, p.id, p.name, p.price
HAVING p.price < AVG(o.amount)
ORDER BY u.name, p.price DESC
LIMIT 50; -- Limit to keep benchmark manageable

-- GOLD STANDARD QUERY 4
-- Description: 3-order moving average analysis.
-- Efficiency: Uses optimized Window Function.
SELECT 
    id as order_id,
    created_at,
    amount,
    ROUND(AVG(amount) OVER (
        ORDER BY created_at 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) as moving_avg_3_orders
FROM orders
ORDER BY created_at
LIMIT 50; -- Limit mainly for visual verification
