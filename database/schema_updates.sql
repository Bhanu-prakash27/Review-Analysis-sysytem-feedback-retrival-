-- database/schema_updates.sql
-- Run this to add product_url column if it doesn't exist

-- Add product_url column to raw_reviews table
ALTER TABLE raw_reviews 
ADD COLUMN IF NOT EXISTS product_url VARCHAR(500) AFTER product_name;

-- Add index for faster filtering by product_url
CREATE INDEX IF NOT EXISTS idx_product_url ON raw_reviews(product_url);

-- Add index for product_name for faster searching
CREATE INDEX IF NOT EXISTS idx_product_name ON raw_reviews(product_name);

-- Verify the changes
DESCRIBE raw_reviews;