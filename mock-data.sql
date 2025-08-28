INSERT INTO customers (name, customer_type, personal_id) VALUES 
('Tony Stark', 'INDIVIDUAL', '203948293'),
('Steve Rogers', 'INDIVIDUAL', '123456789');

INSERT INTO customers (name, customer_type, business_number) VALUES 
('TechnoCorp Ltd.', 'BUSINESS', '514857392');

-- 1 VIP Individual Customer
INSERT INTO customers (name, customer_type, personal_id, vip_tier) VALUES 
('Natasha Romanoff', 'INDIVIDUAL', '987654321', 'Gold');

-- 1 VIP Business Customer
INSERT INTO customers (name, customer_type, business_number, vip_tier) VALUES 
('Stark Industries', 'BUSINESS', '999888777', 'Platinum');

INSERT INTO accounts (customer_id, account_number, account_type, balance, currency) VALUES 
(1, 'ACC-1001', 'CHECKING', 1500.00, 'ILS'),      -- Tony Stark (individual)
(2, 'ACC-1002', 'SAVINGS', 3500.00, 'ILS'),       -- Steve Rogers (individual)  
(3, 'ACC-2002', 'BUSINESS', 8000.00, 'ILS'),      -- TechnoCorp Ltd. (business)
(4, 'ACC-3001', 'VIP', 25000.00, 'ILS'),          -- Natasha Romanoff (VIP individual)
(5, 'ACC-4001', 'VIP', 50000.00, 'ILS');          -- Stark Industries (VIP business)

INSERT INTO transactions (
    transaction_id, from_account_id, to_account_id, 
    from_balance_before, from_balance_after, 
    to_balance_before, to_balance_after,
    amount, currency, description, status, timestamp
) VALUES 
(98765, 1, 3, 1800.00, 1500.00, 7700.00, 8000.00, 300.00, 'ILS',
 'Monthly service payment', 'completed', '2025-07-30 13:45:00'),

(98766, 4, 2, 25500.00, 25000.00, 3000.00, 3500.00, 500.00, 'ILS',
 'VIP consulting payment', 'pending', NOW());