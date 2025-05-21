-- Add is_printed column to bin_count_records table
ALTER TABLE bin_count_records
ADD COLUMN is_printed BOOLEAN DEFAULT FALSE;
 
-- Add comment to the column
COMMENT ON COLUMN bin_count_records.is_printed IS 'Indicates whether the record has been printed (true) or not (false)'; 