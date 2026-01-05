-- Orders Management Schema

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(200),
    customer_phone VARCHAR(20),
    order_type VARCHAR(50) DEFAULT 'dine-in', -- 'dine-in', 'takeaway', 'delivery'
    table_number VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled'
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Order Items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id INTEGER REFERENCES menu_items(id) ON DELETE SET NULL,
    item_name VARCHAR(200) NOT NULL, -- Store name in case item is deleted later
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL, -- quantity * unit_price
    modifiers TEXT, -- Store selected modifiers as JSON or text
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);

-- Update timestamp trigger for orders
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate order total
CREATE OR REPLACE FUNCTION calculate_order_total(p_order_id INTEGER)
RETURNS DECIMAL(10, 2) AS $$
DECLARE
    total DECIMAL(10, 2);
BEGIN
    SELECT COALESCE(SUM(subtotal), 0.00)
    INTO total
    FROM order_items
    WHERE order_id = p_order_id;
    
    UPDATE orders
    SET total_amount = total
    WHERE id = p_order_id;
    
    RETURN total;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update order total when items are added/updated
CREATE OR REPLACE FUNCTION update_order_total()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM calculate_order_total(COALESCE(NEW.order_id, OLD.order_id));
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_order_total_insert
    AFTER INSERT ON order_items
    FOR EACH ROW
    EXECUTE FUNCTION update_order_total();

CREATE TRIGGER trigger_update_order_total_update
    AFTER UPDATE ON order_items
    FOR EACH ROW
    EXECUTE FUNCTION update_order_total();

CREATE TRIGGER trigger_update_order_total_delete
    AFTER DELETE ON order_items
    FOR EACH ROW
    EXECUTE FUNCTION update_order_total();
