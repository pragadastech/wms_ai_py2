from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from supabase import create_client, Client
import os
from typing import Optional, List, Dict
import logging
from pydantic import BaseModel, Field, RootModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Pydantic Models
class ShipLabelItem(BaseModel):
    label_id: int
    label_data: str
    packingslip_data: Optional[str] = ""
    tracking_number: Optional[str] = ""
    sscc_code: str

class LabelData(BaseModel):
    ship_label_data: List[ShipLabelItem] = Field(default_factory=list)

class ItemLabels(RootModel):
    root: Dict[str, LabelData]

class OrderLabels(RootModel):
    root: Dict[str, Dict[str, LabelData]]

def get_supabase_client() -> Client:
    """Initialize and return Supabase client"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not found in environment variables")
    return create_client(supabase_url, supabase_key)

@app.get("/labels/{order_id}", response_model=OrderLabels)
async def get_labels(order_id: str, item_id: Optional[str] = None):
    """
    Fetch label data for a given order_id and optional item_id.
    
    Args:
        order_id (str): The order ID to fetch labels for
        item_id (str, optional): The specific item ID to fetch labels for
        
    Returns:
        Dict containing label data with detailed ship_label_data for each item
    """
    try:
        supabase = get_supabase_client()
        
        # Base query with distinct selection to avoid duplicates
        query = supabase.table("generated-sales-labels").select(
            "item_id",
            "html_with_image_src",
            "label_number",
            "sscc_code",
            "packingslip_data",
            "tracking_number"
        ).eq("order_id", order_id).eq("status", "active").order("label_number")
        
        # Add item_id filter if provided
        if item_id:
            query = query.eq("item_id", item_id)
        
        # Execute query
        response = query.execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"No labels found for order_id: {order_id}")
        
        # Initialize the result structure
        result = {
            order_id: {}
        }
        
        # Track seen images to prevent duplicates
        seen_images = set()
        
        # Group by item_id and ensure unique labels
        for label in response.data:
            current_item_id = label["item_id"]
            html_data = label.get("html_with_image_src")
            
            if not html_data or html_data in seen_images:
                continue
                
            if current_item_id not in result[order_id]:
                result[order_id][current_item_id] = {
                    "ship_label_data": []
                }
            
            # Create ship label item
            ship_label_item = {
                "label_id": label.get("label_number", 0),
                "label_data": html_data,
                "packingslip_data": label.get("packingslip_data") or "",
                "tracking_number": label.get("tracking_number") or "",
                "sscc_code": label.get("sscc_code", "")
            }
            
            # Add to ship_label_data list
            result[order_id][current_item_id]["ship_label_data"].append(ship_label_item)
            seen_images.add(html_data)
        
        # If item_id was provided, only return that specific item
        if item_id:
            if item_id in result[order_id]:
                logger.info(f"Successfully retrieved {len(result[order_id][item_id]['ship_label_data'])} labels for order_id: {order_id}, item_id: {item_id}")
                return {
                    order_id: {
                        item_id: result[order_id][item_id]
                    }
                }
            else:
                raise HTTPException(status_code=404, detail=f"No labels found for item_id: {item_id}")
        
        # Log success message for all items
        for item_id, item_data in result[order_id].items():
            logger.info(f"Successfully retrieved {len(item_data['ship_label_data'])} labels for order_id: {order_id}, item_id: {item_id}")
        
        # Validate response with Pydantic model
        validated_response = OrderLabels(root=result)
        return validated_response
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

