-- RestroBot Database Schema

-- Menu Categories
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Menu Items
CREATE TABLE IF NOT EXISTS menu_items (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2),
    available BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Modifiers (Spice levels, dietary options, add-ons)
CREATE TABLE IF NOT EXISTS modifiers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'spice_level', 'dietary', 'addon', 'custom'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Item-Modifier relationship (which modifiers apply to which items)
CREATE TABLE IF NOT EXISTS item_modifiers (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES menu_items(id) ON DELETE CASCADE,
    modifier_id INTEGER REFERENCES modifiers(id) ON DELETE CASCADE,
    UNIQUE(item_id, modifier_id)
);

-- Special notes and announcements
CREATE TABLE IF NOT EXISTS specials (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Out of stock items
CREATE TABLE IF NOT EXISTS out_of_stock (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(200) NOT NULL,
    expected_back DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_menu_items_category ON menu_items(category_id);
CREATE INDEX idx_menu_items_available ON menu_items(available);
CREATE INDEX idx_modifiers_type ON modifiers(type);
CREATE INDEX idx_specials_active ON specials(active);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_menu_items_updated_at
    BEFORE UPDATE ON menu_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
