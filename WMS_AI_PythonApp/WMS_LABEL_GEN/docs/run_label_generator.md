# Run Label Generator

## Overview
The main application file that handles the generation and processing of shipping labels. This module is responsible for creating SSCC codes, processing addresses, and generating HTML-based shipping labels.

## Features
- SSCC code generation with GS1 check digit calculation
- Shipping address parsing and validation
- HTML-based label generation
- Supabase database integration
- Multi-item and multi-order label processing

## Running the Program

### Prerequisites
1. Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

3. Set up environment variables in `.env`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Running the Application
1. Activate the virtual environment:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

2. Run the program:
```bash
python run_label_generator.py
```

### Expected Output
- The program will process input data and generate labels
- Labels will be saved to `generated_labels.json`
- HTML-based labels will be created for each item
- Progress will be displayed in the console

### Common Issues and Solutions
1. **Playwright Browser Error**
   - Solution: Run `playwright install` to install required browsers

2. **Supabase Connection Error**
   - Solution: Verify `.env` file contains correct credentials

3. **Input Data Format Error**
   - Solution: Ensure input data follows the required structure

## Functions

### `calculate_check_digit_gs1(sscc_code)`
Calculates the GS1 check digit for SSCC codes.
- **Input**: 17-digit SSCC code
- **Output**: Check digit (0-9)
- **Raises**: ValueError if input length is not 17 digits

### `generate_sscc_code(upc_code, line_id, sequence_number=1)`
Generates a unique SSCC code for shipping labels.
- **Input**:
  - `upc_code`: 12-digit UPC code
  - `line_id`: Line identifier
  - `sequence_number`: Optional sequence number (default: 1)
- **Output**: Tuple of (sscc_code, sscc_display)
- **Raises**: ValueError for invalid UPC code length

### `parse_shipping_address(address)`
Parses shipping address string into components.
- **Input**: Multi-line address string
- **Output**: Dictionary with address components:
  - name
  - address1
  - city
  - state
  - zip

### `parse_ship_from(ship_from)`
Processes ship-from address information.
- **Input**: Comma-separated address string
- **Output**: Dictionary with address components
- **Raises**: ValueError for invalid address format

### `generate_all_labels(input_data)`
Main function for generating labels from input data.
- **Input**: Dictionary containing order data
- **Output**: Generated labels data
- **Process**:
  1. Launches Playwright browser
  2. Processes each order
  3. Generates labels for each item
  4. Creates HTML-based labels
  5. Returns processed label data

## Usage Example
```python
# Example input data structure
input_data = {
    "order_id": {
        "shipping_address": "John Doe\n123 Main St\nAnytown, CA 12345",
        "ship_from": "Company Name L41, 456 Warehouse Ave, City, ST 67890",
        "itemDetails": [
            {
                "item": "Product Name",
                "quantity": 2,
                "upc_code": "123456789012"
            }
        ]
    }
}

# Generate labels
labels = await generate_all_labels(input_data)
```

## Dependencies
- playwright
- python-dotenv
- supabase
- math (standard library)
- json (standard library)
- base64 (standard library)

## Error Handling
- Validates input data structure
- Checks for required fields
- Handles address parsing errors
- Manages browser automation errors

## Notes
- Requires Playwright browsers to be installed
- Needs valid Supabase credentials in .env file
- HTML label generation uses specific styling and formatting 