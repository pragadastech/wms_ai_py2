import json
import webbrowser
import tempfile
import os
import base64
import asyncio
from playwright.async_api import async_playwright
import math
from dotenv import load_dotenv
from supabase import create_client, Client
import time

def calculate_check_digit_gs1(sscc_code):
    """Replicate the checkDigitGS1 function from JavaScript"""
    if len(sscc_code) != 17:
        raise ValueError(f"SSCC code must be 17 digits for check digit calculation, got {len(sscc_code)} digits: {sscc_code}")
    
    check_digit_sum = 0
    for i in range(17):
        multiplier = 3 if i % 2 == 0 else 1
        check_digit_sum += int(sscc_code[i]) * multiplier
    
    check_digit = (math.ceil(check_digit_sum / 10) * 10) - check_digit_sum
    return check_digit

def generate_sscc_code(upc_code, line_id, sequence_number=1):
    """Generate SSCC code following the exact JavaScript implementation"""
    # Extension digit (0-9)
    extension_digit = "0"
    
    # Extract GS1 Company Prefix from UPC
    if len(upc_code) == 12:  # Standard UPC-A
        first_chars = upc_code[:2]
        if first_chars == "84":  # Special case from JS
            gs1_prefix = upc_code[:9]  # Take first 9 digits for 840 prefix
        else:
            gs1_prefix = upc_code[:9]  # Take first 9 digits
    else:
        raise ValueError(f"Invalid UPC code length: {len(upc_code)}")
    
    # Format line_id and sequence number to ensure uniqueness
    # Using a fixed serial reference format that matches the system
    serial_ref = "62229"  # Fixed prefix from system examples
    serial_ref += str(line_id).zfill(2)  # Pad line_id to 2 digits
    serial_ref += str(sequence_number).zfill(1)  # Add sequence number
    
    # Combine parts to create 17-digit base (extension_digit + gs1_prefix + serial_ref)
    sscc_base = f"{extension_digit}{gs1_prefix}{serial_ref}"
    
    # Ensure base is exactly 17 digits
    if len(sscc_base) > 17:
        sscc_base = sscc_base[-17:]  # Take last 17 digits if too long
    elif len(sscc_base) < 17:
        sscc_base = sscc_base.zfill(17)
    
    # Calculate check digit
    check_digit = calculate_check_digit_gs1(sscc_base)
    
    # Return complete 18-digit SSCC with "0000" prefix
    sscc_code = f"0000{sscc_base}{check_digit}"
    # Format display to show (00) followed by the numbers
    sscc_display = f"(00) {sscc_code[2:12]}&nbsp;{sscc_code[12:]}"
    
    return sscc_code, sscc_display

def parse_shipping_address(address):
    """Parse shipping address string into components"""
    lines = address.split('\n')
    name = lines[0]
    address1 = lines[2]
    city_state_zip = lines[3]
    
    # Extract city, state, and zip
    city_state_zip_parts = city_state_zip.split(' ')
    # Remove empty strings from the split
    city_state_zip_parts = [part for part in city_state_zip_parts if part]
    
    # The last two parts should be state and zip
    state = city_state_zip_parts[-2]
    zip_code = city_state_zip_parts[-1]
    # Everything before state and zip is the city
    city = ' '.join(city_state_zip_parts[:-2])
    
    return {
        "name": name,
        "address1": address1,
        "city": city,
        "state": state,
        "zip": zip_code
    }

def parse_ship_from(ship_from):
    """Parse ship from address string into components"""
    # Split the address into parts
    parts = ship_from.split(', ')
    if len(parts) < 3:
        raise ValueError(f"Invalid ship from address format: {ship_from}")
    
    # The first part contains the company name and location
    company_location = parts[0]
    # Split company name and location - handle both L41 and L60 formats
    if ' L41' in company_location:
        company_parts = company_location.split(' L41')
    elif ' L60' in company_location:
        company_parts = company_location.split(' L60')
    else:
        # If no location code is found, use the whole string as company name
        company_parts = [company_location, '']
    
    if len(company_parts) != 2:
        company_name = company_location
    else:
        company_name = company_parts[0]
    
    address1 = parts[1]
    city = parts[2]
    state_zip = parts[3].split(' ')
    state = state_zip[0]
    zip_code = state_zip[1]
    
    return {
        "name": company_name,
        "address1": address1,
        "city": city,
        "state": state,
        "zip": zip_code
    }

async def generate_all_labels(input_data):
    """Generate labels from input data and return the labels data"""
    # Create a dictionary to store labels by item
    labels_by_item = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Set viewport size to match label dimensions
        await page.set_viewport_size({"width": 384, "height": 576})
        
        # Process all orders in the input data
        for order_id, order_data in input_data.items():
            print(f"\nProcessing order: {order_id}")
            print(f"Order data structure: {json.dumps(order_data, indent=2)}")
            
            # Check if itemDetails exists
            if "itemDetails" not in order_data:
                print(f"Warning: No itemDetails found for order {order_id}. Skipping this order.")
                continue
                
            # Parse addresses
            if "shipping_address" not in order_data or "ship_from" not in order_data:
                print(f"Warning: Missing shipping address or ship from address for order {order_id}. Skipping this order.")
                continue
                
            shipping_address = parse_shipping_address(order_data["shipping_address"])
            ship_from = parse_ship_from(order_data["ship_from"])
            
            # Process all items in the order
            for item_index, item_details in enumerate(order_data["itemDetails"]):
                item_name = item_details["item"]
                quantity = int(item_details["quantity"])
                # Use quantity as total_cartons if not specified
                total_cartons = int(item_details.get("total_cartons", quantity))
                
                print(f"\nProcessing item: {item_name} (Quantity: {quantity}, Total Cartons: {total_cartons})")
                
                # Process each label for this item
                for label_count in range(quantity):
                    # Calculate carton index for this label
                    carton_index = (label_count % total_cartons) + 1
                    
                    # Generate unique SSCC code using the line ID and label count
                    sscc_code, sscc_display = generate_sscc_code(
                        item_details["upc_code"],
                        item_index + 1,
                        label_count + 1
                    )
                    
                    if "L60" in ship_from["name"]:
                        order_data["ponumber"] = order_data["ponumber"] + "-SC"
                    
                    # Create label HTML
                    label_html = f"""
<html>
<head>
    <title>Shipping Label</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jsbarcode/3.11.0/JsBarcode.all.min.js"></script>
    <link href='https://fonts.googleapis.com/css?family=Libre Barcode 39' rel='stylesheet'>
    <style>
        .cisr {{ font-size: 20px; text-align: center; }}
        .rght {{ text-align: right; }}
        .massprint {{ height: 100px; border-right: none; border-left: none; border-bottom: none; }}
        .so {{ height: 100px; border-right: none; border-left: none; }}
        .units {{ height: 100px; border-top: none; border-right: none; border-left: none; }}
        .vl {{ border-left: 2px solid; height: 40px; }}
        td {{ padding: 1px 2px 4px 7px; font-size:12px; line-height: 14px; width: 50%; }}
        .laddress {{ max-width: 180px; font-size: 12px; }}
    </style>
</head>
<body>
<div style="width:384px;height: 576px;font-family: system-ui;">
    <table class="units" cellpadding="0" style="width:384px;max-height:150px;border:0px solid #000;">
        <tr style='height:40px;vertical-align:top;'>
            <td class="pleft" style="text-align:left;">
                <div class="laddress">
                    <b>SHIP FROM:</b><br><br>
                    {ship_from["name"]}<br>
                    {ship_from["address1"]},<br>
                    {ship_from["city"]},   {ship_from["state"]} {ship_from["zip"]}<br><br><br>
                </div>
            </td>
            <td class='vl' style='width: 1px;background: #000;padding: 0;'></td>
            <td class="pleft" style="text-align:left;">
                <div class="">
                    <b>SHIP TO:</b><br><br>
                    {shipping_address["name"]}<br>
                    {shipping_address["address1"]}<br>
                    {shipping_address["city"]},   {shipping_address["state"]} {shipping_address["zip"]}<br><br><br>
                </div>
            </td>
        </tr>
    </table>
    <hr style="height:2px;color: black;background-color: black;margin: 0 0 10px 0;">
    <table class="units" cellpadding="0" style="width:384px;max-height:150px;border:0px solid #000;">
        <tr style='height:40px;vertical-align:top;'>
            <td class="pleft" style="text-align:left;width:50%;">
                <div class="laddress" style="line-height: 30px;">
                    <img id="barcodeprint" style="width:175px;height: 60px;"  />
                    <script>JsBarcode("#barcodeprint", "420{shipping_address['zip'][:5]}", {{format: "CODE128",displayValue: false}});</script>
                    <figcaption style='text-align:center;font-size: 20px;'>(420) {shipping_address["zip"][:5]}</figcaption>
                </div>
            </td>
            <td class='vl' style='width: 1px;background: #000;padding: 0;'></td>
            <td class="pleft" style="text-align:left;width:50%;">
                <div class="">
                    <b>Amazon Freight LTL</b><br>
                    <b>Pro# :</b> <br>
                    <b>BOL# : </b> {order_data.get("reference_1", "")}
                </div>
            </td>
        </tr>
    </table>
    <hr style="height:2px;color: black;background-color: black;margin: 0 0 10px 0;">
    <table class="units" style="width:100%;max-height:250px;border:0px solid #000;">
        <tr style='text-align:left;'>
            <td class="pleft"><b>PO#</b> {order_data["ponumber"]}</td>
            <td>
                <div>
                    <img id="barcode1" height="60px" width="100%" />
                    <script>JsBarcode("#barcode1", "{order_data['ponumber']}", {{format: "CODE128",displayValue: false}});</script>
                </div>
            </td>
        </tr>
        <tr style='text-align:left;'>
            <td class="pleft" colspan="2"><b>UPC: </b>{item_details["upc_code"]} / SINGLE ASIN</td>
        </tr>
        <tr style='text-align:left;'>
            <td class="pleft"><b>QTY: </b>{item_details["quantity"]}</td>
        </tr>
        <tr style='text-align:left;'>
            <td class="pleft" colspan="2"><b>CARTON: {carton_index} of {total_cartons}</b></td>
        </tr>
        <tr style='text-align:left;'>
            <td class="pleft" colspan="2"><b>MODEL: </b>{item_name}</td>
        </tr>
        <tr><td></td></tr>
    </table>
    <hr style="height:2px;color: black;background-color: black;">
    <table class=''>
        <tr>
            <td style='float:left;'>SSCC - 18</td>
        </tr>
        <tr>
            <td>
                <div style='text-align: center;line-height: 30px;'>
                    <img id="barcode2" height="75px" width="360px" />
                    <script>JsBarcode("#barcode2", "{sscc_code}", {{format: "CODE128",displayValue: false}});</script>
                    <figcaption style='text-align:center;font-size: 17px;'>{sscc_display}</figcaption>
                </div>
            </td>
        </tr>
    </table>
</div>
</body>
</html>
"""
                    
                    # Create label HTML
                    packingslip_html = f"""
                    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css?family=Source+Serif+Pro&display=swap');
            table {{
                font-family: 'Source Serif Pro', serif;
                border-collapse: collapse;
                width: 100%;
            }}
            td,
            th {{
                padding: 5px;
            }}
            #tbl-data-add tbody p {{
                font-size: 12px;
                font-weight: bold;
                margin: 3px 0px;
            }}
            #tbl-data-add1 {{
                border-collapse: collapse;
                border: 1px solid #ddd;
            }}
            #tbl-data-add1 tr {{
                border-bottom: 1px solid #ddd;
            }}
            #tbl-data-add1 td {{
                border: 1px solid #ddd;
                font-size: 12px;
                padding: 1px;
            }}
            #tbl-data-add1 th {{
                border: 1px solid #ddd;
                font-size: 12px;
                padding: 1px;
            }}
            #tbl-data-add1 thead {{
                background: #eee;
            }}
        </style>
    </head>
    <body style="width: 373px; height: 576px; padding: 2px;">
        <table style="height: 100%;">
            <tr>
                <td style="vertical-align: middle; text-align: center;">
                    <p style="font-size: 28px; font-weight: bold;">AMAZON P/U ORDERS</p>
                    <p style="font-size: 40px; font-weight: bold;">PO#{order_data["ponumber"]}</p>
                </td>
            </tr>
        </table>
    </body>
</html>
                    """
                    
                    # Convert packingslip_html to base64
                    packingslip_base64 = base64.b64encode(packingslip_html.encode('utf-8')).decode('utf-8')
                    
                    # Create a temporary HTML file for the current label
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
                        f.write(label_html)
                        temp_html_path = f.name
                    
                    try:
                        # Load the HTML file
                        await page.goto('file://' + os.path.realpath(temp_html_path))
                        
                        # Wait for JavaScript to render
                        await page.wait_for_timeout(2000)
                        
                        # Take screenshot
                        screenshot_bytes = await page.screenshot()
                        
                        # Store in labels_by_item dictionary
                        if item_name not in labels_by_item:
                            labels_by_item[item_name] = {
                                "labels": [],
                                "quantity": quantity
                            }
                        
                        label_data = {
                            "label_number": label_count + 1,
                            "carton_index": carton_index,
                            "total_cartons": total_cartons,
                            "sscc_code": sscc_code,
                            "sscc_display": sscc_display,
                            "html_base64": base64.b64encode(label_html.encode('utf-8')).decode('utf-8'),
                            "image_base64": base64.b64encode(screenshot_bytes).decode('utf-8'),
                            "html_with_image_src": base64.b64encode(f'<html><div><img style="width:373px; height:576px" src="data:image/png;base64,{base64.b64encode(screenshot_bytes).decode("utf-8")}"/></div></html>'.encode('utf-8')).decode('utf-8'),
                            "packingslip_data": packingslip_base64
                        }
                        
                        labels_by_item[item_name]["labels"].append(label_data)
                        
                        # Print SSCC code and carton info for verification
                        print(f"Generated SSCC code for {item_name} (Label {label_count + 1}/{quantity}, Carton {carton_index}/{total_cartons}): {sscc_code}")
                        
                    finally:
                        # Clean up temporary file
                        os.unlink(temp_html_path)
        
        await browser.close()
        
        return labels_by_item

def generate_labels(input_data):
    """Main function to generate labels from input data"""
    return asyncio.run(generate_all_labels(input_data))

# --- Supabase client and fetch function ---
def get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not found in environment variables")
    return create_client(supabase_url, supabase_key)

def fetch_sales_orders_from_supabase(table_name: str = "netsuite_sales_orders") -> dict:
    """
    Fetch sales orders from Supabase table and return a dictionary mapping internal_id to sales_order_data.
    """
    supabase = get_supabase_client()
    response = supabase.table(table_name).select("*").execute()
    sales_orders_data = {}
    for order in response.data:
        internal_id = str(order.get("internal_id", ""))
        sales_order_data = order.get("sales_order_data", {})
        if internal_id and sales_order_data:
            sales_orders_data[internal_id] = sales_order_data
    return sales_orders_data
# --- End Supabase logic ---

def store_labels_in_supabase(labels_data: dict, internal_id: str, order_id: str) -> None:
    """
    Store labels in the generated-sales-labels table.
    Each label will be stored as a separate row.
    """
    supabase = get_supabase_client()
    
    try:
        print(f"\nAttempting to store labels for internal_id: {internal_id}")
        
        # Process each item's labels
        for item_id, item_data in labels_data.items():
            if "labels" in item_data:
                for label in item_data["labels"]:
                    try:
                        # Prepare label data for SQL storage
                        label_row = {
                            "internal_id": internal_id,
                            "order_id": order_id,
                            "item_id": item_id,
                            "item_name": item_data.get("item_name", item_id),  # Use item_id as fallback
                            "label_number": label.get("label_number"),
                            "carton_index": label.get("carton_index"),
                            "total_cartons": label.get("total_cartons"),
                            "sscc_code": label.get("sscc_code"),
                            "sscc_display": label.get("sscc_display"),
                            "html_base64": label.get("html_base64"),
                            "image_base64": label.get("image_base64"),
                            "html_with_image_src": label.get("html_with_image_src"),
                            "packingslip_data": label.get("packingslip_data"),
                            "status": "active"
                        }
                        
                        # Insert the label into the generated-sales-labels table
                        response = supabase.table("generated-sales-labels").insert(label_row).execute()
                        
                        if hasattr(response, 'error') and response.error:
                            print(f"Error storing label for item {item_id}: {response.error}")
                        else:
                            print(f"Successfully stored label {label.get('label_number')} for item {item_id}")
                            
                    except Exception as e:
                        print(f"Error processing label for item {item_id}: {str(e)}")
                        continue
        
        print(f"Completed storing labels for internal_id {internal_id}")
        
    except Exception as e:
        print(f"Error storing labels: {str(e)}")
        raise

async def main():
    load_dotenv()
    try:
        print("Fetching sales orders from Supabase...")
        orders_data = fetch_sales_orders_from_supabase()
        if not orders_data:
            print("No sales orders found")
            return
            
        print(f"Found {len(orders_data)} sales orders")
        print("Generating labels...")
        labels_data = await generate_all_labels(orders_data)
        
        print("\nStoring labels in Supabase...")
        for internal_id, order_data in orders_data.items():
            print(f"\nProcessing internal_id: {internal_id}")
            
            # Get all items for this order from itemDetails
            order_items = [item["item"] for item in order_data.get("itemDetails", [])]
            print(f"Items in order: {order_items}")
            
            # Get labels for items in this order
            order_labels = {}
            for item_id in order_items:
                if item_id in labels_data:
                    order_labels[item_id] = labels_data[item_id]
            
            if order_labels:
                print(f"Found {len(order_labels)} items with labels for internal_id {internal_id}")
                print(f"Items with labels: {list(order_labels.keys())}")
                
                try:
                    # Pass both internal_id and order_id to the storage function
                    store_labels_in_supabase(order_labels, internal_id, order_data.get("order_id", internal_id))
                except Exception as e:
                    print(f"Error storing labels in database: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"No labels found for internal_id {internal_id}")
        
        print("\nLabel storage process completed")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())