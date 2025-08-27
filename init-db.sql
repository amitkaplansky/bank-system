
USE banking_db;

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    customer_type ENUM('individual', 'business') NOT NULL,
    
    -- Individual customer fields
    personal_id VARCHAR(20) NULL,
    
    -- Business customer fields  
    business_number VARCHAR(20) NULL,
    
    -- VIP tier (can be applied to both individual and business customers)
    vip_tier VARCHAR(50) NULL COMMENT 'Gold, Platinum, Diamond - null for regular customers',
    
    email VARCHAR(255) NULL,
    phone VARCHAR(20) NULL,
    address TEXT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_personal_id (personal_id),
    UNIQUE KEY unique_business_number (business_number),
    
    CONSTRAINT check_individual_fields 
        CHECK (customer_type != 'individual' OR personal_id IS NOT NULL),
    CONSTRAINT check_business_fields 
        CHECK (customer_type != 'business' OR business_number IS NOT NULL)
);

CREATE TABLE accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    account_number VARCHAR(50) NOT NULL UNIQUE,
    account_type ENUM('checking', 'savings', 'business', 'vip') NOT NULL DEFAULT 'checking',
    balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'ILS',
    status ENUM('active', 'inactive', 'frozen', 'closed') NOT NULL DEFAULT 'active',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    
    INDEX idx_customer_id (customer_id),
    INDEX idx_account_number (account_number),
    INDEX idx_status (status)
);

CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id BIGINT NOT NULL UNIQUE,
    
    from_account_id INT NOT NULL,
    to_account_id INT NOT NULL,
    
    from_balance_before DECIMAL(15,2) NOT NULL,
    from_balance_after DECIMAL(15,2) NOT NULL,
    to_balance_before DECIMAL(15,2) NOT NULL, 
    to_balance_after DECIMAL(15,2) NOT NULL,
    
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'ILS',
    description TEXT NULL,
    
    status ENUM('pending', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'pending',
    processed_by VARCHAR(100) DEFAULT 'bank-core-service',
    source VARCHAR(100) DEFAULT 'api/v1/transfer',
    
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (from_account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (to_account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_from_account (from_account_id),
    INDEX idx_to_account (to_account_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (status),
    
    -- Prevent negative balances after transaction
    CONSTRAINT check_positive_balances 
        CHECK (from_balance_after >= 0 AND to_balance_after >= 0),
    
    -- Ensure transaction amount is positive
    CONSTRAINT check_positive_amount 
        CHECK (amount > 0),
        
    -- Prevent self-transfer
    CONSTRAINT check_different_accounts 
        CHECK (from_account_id != to_account_id)
);

CREATE INDEX idx_customer_type ON customers(customer_type);
CREATE INDEX idx_account_balance ON accounts(balance);
CREATE INDEX idx_transaction_amount ON transactions(amount);
CREATE INDEX idx_transaction_date ON transactions(timestamp);
