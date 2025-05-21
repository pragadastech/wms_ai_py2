-- Rename the admin_john table to master_admin_details
ALTER TABLE admin_john RENAME TO master_admin_details;

-- Rename the constraints to match the new table name
ALTER TABLE master_admin_details 
RENAME CONSTRAINT unique_company_email TO master_admin_unique_company_email;

ALTER TABLE master_admin_details 
RENAME CONSTRAINT unique_phone_number TO master_admin_unique_phone_number; 