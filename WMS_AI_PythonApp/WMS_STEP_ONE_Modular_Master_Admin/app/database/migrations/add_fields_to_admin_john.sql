-- Add new columns to admin_john table
ALTER TABLE admin_john
ADD COLUMN company_name VARCHAR(255),
ADD COLUMN company_email VARCHAR(255),
ADD COLUMN phone_number VARCHAR(20),
ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add comments to the columns
COMMENT ON COLUMN admin_john.company_name IS 'Name of the company the admin belongs to';
COMMENT ON COLUMN admin_john.company_email IS 'Company email address of the admin';
COMMENT ON COLUMN admin_john.phone_number IS 'Contact phone number of the admin';
COMMENT ON COLUMN admin_john.created_at IS 'Timestamp when the admin was registered';

-- Add unique constraints
ALTER TABLE admin_john
ADD CONSTRAINT unique_company_email UNIQUE (company_email),
ADD CONSTRAINT unique_phone_number UNIQUE (phone_number); 