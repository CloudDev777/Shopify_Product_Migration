import httpx
from typing import Dict, List, Optional, Any
import logging
from rich.logging import RichHandler
import json

# Configure rich logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("shopify_client")


class ShopifyClient:
    """A client for interacting with the Shopify Admin API."""
    
    def __init__(self, store_url: str, admin_key: str):
        """
        Initialize the Shopify client.
        
        Args:
            store_url: The store's myshopify.com URL
            admin_key: The Admin API access token
        """
        if not all([store_url, admin_key]):
            raise ValueError("All credentials (store_url, admin_key) must be provided")
        
        if not store_url.endswith('myshopify.com'):
            raise ValueError("Store URL must end with 'myshopify.com'")
            
        self.store_url = store_url
        self.base_url = f"https://{store_url}/admin/api/2024-01"
        self.headers = {
            "X-Shopify-Access-Token": admin_key,
            "Content-Type": "application/json"
        }
        log.info(f"Initialized Shopify client for store: {store_url}")
    
    async def validate_credentials(self) -> bool:
        """
        Validate the API credentials by making a test request.
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/shop.json",
                    headers=self.headers
                )
                response.raise_for_status()
                log.info(f"Successfully validated credentials for store: {self.store_url}")
                return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                log.error(f"Invalid admin access token for store {self.store_url}. Please check your Admin API access token.")
            else:
                log.error(f"HTTP error during credential validation: {str(e)}")
            return False
        except Exception as e:
            log.error(f"Error validating credentials: {str(e)}")
            return False
    
    async def get_products(self, limit: int = 250) -> List[Dict]:
        """
        Retrieve products from the store with complete data including variants and images.
        
        Args:
            limit: Maximum number of products to retrieve per request
            
        Returns:
            List of product dictionaries
        """
        log.info(f"Fetching products from {self.store_url} (limit: {limit})")
        
        try:
            # Validate credentials first
            if not await self.validate_credentials():
                raise ValueError(f"Invalid credentials for store {self.store_url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/products.json",
                    params={
                        "limit": limit,
                        "fields": "id,title,body_html,vendor,product_type,handle,status,variants,images,options"
                    },
                    headers=self.headers
                )
                response.raise_for_status()
                
                # Parse the response JSON
                response_data = response.json()
                if not isinstance(response_data, dict) or "products" not in response_data:
                    raise ValueError("Invalid response format from Shopify API")
                
                products = response_data["products"]
                log.info(f"Retrieved {len(products)} products from {self.store_url}")
                
                # Validate product data
                for product in products:
                    if not isinstance(product, dict) or "id" not in product:
                        log.warning("Found invalid product data in response")
                        continue
                
                return products
                
        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error occurred while fetching products: {str(e)}")
            if e.response.status_code == 429:
                log.error("Rate limit exceeded. Please wait before retrying.")
            raise
        except ValueError as e:
            log.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Unexpected error while fetching products: {str(e)}")
            raise
    
    async def create_product(self, product_data: Dict) -> Dict:
        """
        Create a new product in the store with all its variants and images.
        
        Args:
            product_data: Dictionary containing complete product information
            
        Returns:
            Created product data
        """
        title = product_data.get("title", "Unknown")
        log.info(f"Creating product '{title}' in {self.store_url}")
        
        # Clean up the product data to ensure proper creation
        clean_data = self._prepare_product_data(product_data)
        log.debug(f"Cleaned product data: {json.dumps(clean_data, indent=2)}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/products.json",
                    json={"product": clean_data},
                    headers=self.headers
                )
                response.raise_for_status()
                
                # Parse the response JSON
                response_data = response.json()
                if not isinstance(response_data, dict) or "product" not in response_data:
                    raise ValueError("Invalid response format from Shopify API")
                
                created_product = response_data["product"]
                log.info(f"Successfully created product '{created_product['title']}' (ID: {created_product['id']})")
                return created_product
                
        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error occurred while creating product '{title}': {str(e)}")
            if e.response.status_code == 422:
                log.error(f"Validation error from Shopify API: {e.response.text}")
            raise
        except ValueError as e:
            log.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Unexpected error while creating product '{title}': {str(e)}")
            raise
    
    async def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """
        Update an existing product in the store with all its variants and images.
        
        Args:
            product_id: ID of the product to update
            product_data: Dictionary containing updated product information
            
        Returns:
            Updated product data
        """
        title = product_data.get("title", "Unknown")
        log.info(f"Updating product '{title}' (ID: {product_id}) in {self.store_url}")
        
        # Clean up the product data to ensure proper update
        clean_data = self._prepare_product_data(product_data)
        log.debug(f"Cleaned product data: {json.dumps(clean_data, indent=2)}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/products/{product_id}.json",
                    json={"product": clean_data},
                    headers=self.headers
                )
                response.raise_for_status()
                
                # Parse the response JSON
                response_data = response.json()
                if not isinstance(response_data, dict) or "product" not in response_data:
                    raise ValueError("Invalid response format from Shopify API")
                
                updated_product = response_data["product"]
                log.info(f"Successfully updated product '{updated_product['title']}' (ID: {product_id})")
                return updated_product
                
        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error occurred while updating product {product_id}: {str(e)}")
            if e.response.status_code == 422:
                log.error(f"Validation error from Shopify API: {e.response.text}")
            raise
        except ValueError as e:
            log.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Unexpected error while updating product {product_id}: {str(e)}")
            raise
    
    async def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """
        Find a product by its SKU.
        
        Args:
            sku: The SKU to search for
            
        Returns:
            Product data if found, None otherwise
        """
        log.info(f"Searching for product with SKU '{sku}' in {self.store_url}")
        try:
            products = await self.get_products()
            for product in products:
                for variant in product.get("variants", []):
                    if variant.get("sku") == sku:
                        log.info(f"Found product '{product['title']}' with SKU '{sku}'")
                        return product
            log.info(f"No product found with SKU '{sku}'")
            return None
        except Exception as e:
            log.error(f"Error while searching for product with SKU '{sku}': {str(e)}")
            raise
    
    def _prepare_product_data(self, product_data: Dict) -> Dict:
        """
        Prepare product data for API submission by cleaning up unnecessary fields.
        
        Args:
            product_data: Raw product data
            
        Returns:
            Cleaned product data ready for API submission
        """
        # Fields to keep in the product data
        allowed_fields = {
            "title", "body_html", "vendor", "product_type", "handle", 
            "status", "variants", "images", "options"
        }
        
        # Clean the main product data
        cleaned_data = {k: v for k, v in product_data.items() if k in allowed_fields}
        
        # Clean variants data
        if "variants" in cleaned_data:
            variant_count = len(cleaned_data["variants"])
            log.debug(f"Cleaning {variant_count} variants")
            for variant in cleaned_data["variants"]:
                # Remove any variant-specific fields that shouldn't be included in creation/update
                keys_to_remove = ["admin_graphql_api_id", "product_id", "id", "image_id", "inventory_item_id", "old_inventory_quantity", "requires_shipping"]
                for key in keys_to_remove:
                    variant.pop(key, None)
        
        # Clean images data
        if "images" in cleaned_data:
            image_count = len(cleaned_data["images"])
            log.debug(f"Cleaning {image_count} images")
            cleaned_images = []
            for image in cleaned_data["images"]:
                if "src" in image:
                    # Keep only the image URL and alt text
                    cleaned_image = {
                        "src": image["src"],
                        "alt": image.get("alt", "")
                    }
                    # Remove all other fields
                    cleaned_images.append(cleaned_image)
            cleaned_data["images"] = cleaned_images
            log.debug(f"Cleaned {len(cleaned_images)} images")
        
        return cleaned_data 
    
    async def get_collections(self) -> List[Dict[str, Any]]:
        """Get all custom collections from the store."""
        try:
            await self.validate_credentials()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/custom_collections.json",
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict) or "custom_collections" not in data:
                    raise ValueError("Invalid response format for collections")
                log.info(f"Retrieved {len(data['custom_collections'])} collections from {self.store_url}")
                return data["custom_collections"]
        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error occurred while fetching collections: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error fetching collections: {str(e)}")
            raise

    async def get_collection_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Find a collection by its title."""
        try:
            collections = await self.get_collections()
            for collection in collections:
                if collection.get("title") == title:
                    return collection
            return None
        except Exception as e:
            log.error(f"Error finding collection by title: {str(e)}")
            raise

    async def create_collection(self, title: str, description: str = "") -> Dict[str, Any]:
        """Create a new custom collection."""
        try:
            await self.validate_credentials()
            collection_data = {
                "custom_collection": {
                    "title": title,
                    "body_html": description,
                }
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/custom_collections.json",
                    headers=self.headers,
                    json=collection_data,
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict) or "custom_collection" not in data:
                    raise ValueError("Invalid response format for collection creation")
                log.info(f"Created collection '{title}' in {self.store_url}")
                return data["custom_collection"]
        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error occurred while creating collection: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error creating collection: {str(e)}")
            raise

    async def get_product_collections(self, product_id: int) -> List[Dict[str, Any]]:
        """Get all collections that a product belongs to."""
        try:
            await self.validate_credentials()
            collections = await self.get_collections()
            product_collections = []
            
            async with httpx.AsyncClient() as client:
                for collection in collections:
                    response = await client.get(
                        f"{self.base_url}/collects.json?product_id={product_id}&collection_id={collection['id']}",
                        headers=self.headers,
                    )
                    response.raise_for_status()
                    data = response.json()
                    if not isinstance(data, dict) or "collects" not in data:
                        continue
                    
                    if data["collects"]:
                        product_collections.append(collection)
            
            log.info(f"Found {len(product_collections)} collections for product {product_id}")
            return product_collections
        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error occurred while fetching product collections: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error fetching product collections: {str(e)}")
            raise

    async def add_product_to_collection(self, product_id: int, collection_id: int) -> Dict[str, Any]:
        """Add a product to a collection using a collect."""
        try:
            await self.validate_credentials()
            collect_data = {
                "collect": {
                    "product_id": product_id,
                    "collection_id": collection_id,
                }
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/collects.json",
                    headers=self.headers,
                    json=collect_data,
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict) or "collect" not in data:
                    raise ValueError("Invalid response format for collect creation")
                log.info(f"Added product {product_id} to collection {collection_id}")
                return data["collect"]
        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error occurred while adding product to collection: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error adding product to collection: {str(e)}")
            raise 