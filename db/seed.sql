-- Seed data for RestroBot database

-- Insert Categories
INSERT INTO categories (name, display_order) VALUES
    ('Starters', 1),
    ('Main Courses', 2),
    ('Desserts', 3),
    ('Beverages', 4);

-- Insert Starters
INSERT INTO menu_items (category_id, name, description, price, available) VALUES
    (1, 'Garlic Bread', 'Crispy bread with garlic butter', 5.99, true),
    (1, 'Tomato Basil Soup', 'Fresh tomato soup with basil', 6.99, true),
    (1, 'Caesar Salad', 'Romaine lettuce with Caesar dressing', 8.99, true),
    (1, 'Mozzarella Sticks', 'Breaded mozzarella with marinara sauce', 7.99, true);

-- Insert Main Courses
INSERT INTO menu_items (category_id, name, description, price, available) VALUES
    (2, 'Grilled Chicken Alfredo', 'Creamy alfredo pasta with grilled chicken', 16.99, true),
    (2, 'Margherita Pizza', 'Classic pizza with tomato, mozzarella, and basil', 14.99, true),
    (2, 'Veggie Burger with Fries', 'Plant-based burger with crispy fries', 12.99, true),
    (2, 'Spaghetti Bolognese', 'Traditional Italian pasta with meat sauce', 15.99, true),
    (2, 'Paneer Butter Masala with Naan', 'Indian paneer curry with naan bread', 14.99, true),
    (2, 'Butter Chicken with Rice', 'Creamy chicken curry with basmati rice', 16.99, true),
    (2, 'BBQ Chicken', 'Grilled chicken with BBQ sauce', 15.99, true),
    (2, 'Fish and Chips', 'Battered fish with french fries', 17.99, true);

-- Insert Desserts
INSERT INTO menu_items (category_id, name, description, price, available) VALUES
    (3, 'Chocolate Lava Cake', 'Warm chocolate cake with molten center', 7.99, true),
    (3, 'Vanilla Ice Cream Sundae', 'Classic vanilla ice cream with toppings', 6.99, true),
    (3, 'Tiramisu', 'Italian coffee-flavored dessert', 8.99, true),
    (3, 'Gulab Jamun', 'Indian sweet dumplings in syrup', 5.99, true),
    (3, 'Three Milk Cake', 'Latin American sponge cake', 7.99, true);

-- Insert Beverages
INSERT INTO menu_items (category_id, name, description, price, available) VALUES
    (4, 'Fresh Lime Soda', 'Refreshing lime drink', 3.99, true),
    (4, 'Soft Drinks (Coke)', 'Coca-Cola', 2.99, true),
    (4, 'Soft Drinks (Sprite)', 'Sprite', 2.99, true),
    (4, 'Soft Drinks (Fanta)', 'Fanta Orange', 2.99, true),
    (4, 'Iced Tea (Lemon)', 'Cold lemon tea', 3.99, true),
    (4, 'Iced Tea (Peach)', 'Cold peach tea', 3.99, true),
    (4, 'Bottled Water', 'Purified water', 1.99, true);

-- Insert Modifiers
INSERT INTO modifiers (name, type, description) VALUES
    -- Spice Levels
    ('Mild', 'spice_level', 'Light spice level'),
    ('Medium', 'spice_level', 'Medium spice level'),
    ('Spicy', 'spice_level', 'Hot and spicy'),
    
    -- Dietary Options
    ('Vegan', 'dietary', 'Plant-based, no animal products'),
    ('Gluten-Free', 'dietary', 'No gluten ingredients'),
    ('Jain', 'dietary', 'No root vegetables'),
    
    -- Add-ons
    ('Extra Cheese', 'addon', 'Additional cheese'),
    ('Extra Sauce', 'addon', 'Extra sauce on the side'),
    ('Side Salad', 'addon', 'Small side salad'),
    
    -- Custom
    ('No Onions', 'custom', 'Remove onions'),
    ('Extra Crispy', 'custom', 'Cook until extra crispy'),
    ('Gravy on the Side', 'custom', 'Gravy served separately');

-- Insert Specials
INSERT INTO specials (title, description, active) VALUES
    ('Chef''s Special Pasta', 'Only available on weekends', true),
    ('Thali Combo', 'Available from 12 PM to 3 PM', true);

-- Insert Out of Stock items
INSERT INTO out_of_stock (item_name, expected_back) VALUES
    ('Mushroom Soup', CURRENT_DATE + INTERVAL '2 days'),
    ('Orange Juice', CURRENT_DATE + INTERVAL '1 day');
