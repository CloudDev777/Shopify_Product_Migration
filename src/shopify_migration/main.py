import asyncio
import os
from dotenv import load_dotenv
import logging
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Confirm
from shopify_migration.shopify_client import ShopifyClient

# Configure rich logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("shopify_migration")

async def migrate_products(source_client: ShopifyClient, dest_client: ShopifyClient):
    """
    Migrate products from source store to destination store.
    
    Args:
        source_client: ShopifyClient instance for source store
        dest_client: ShopifyClient instance for destination store
    """
    try:
        # Get all products from source store
        log.info("Starting product migration process")
        source_products = await source_client.get_products()
        total_products = len(source_products)
        log.info(f"Found {total_products} products to migrate")
        
        # Initialize progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            migrate_task = progress.add_task(
                "Migrating products...",
                total=total_products
            )
            
            # Track statistics
            created_count = 0
            updated_count = 0
            skipped_count = 0
            error_count = 0
            collection_count = 0
            
            # Keep track of migrated products and their collections
            product_collections = {}
            
            for product in source_products:
                try:
                    # Check if product exists in destination store by SKU
                    variants = product.get("variants", [])
                    if not variants:
                        log.warning(f"Skipping product '{product.get('title', 'Unknown')}' - No variants found")
                        skipped_count += 1
                        progress.advance(migrate_task)
                        continue

                    sku = variants[0].get("sku")
                    if not sku:
                        log.warning(f"Skipping product '{product.get('title', 'Unknown')}' - No SKU found in first variant")
                        skipped_count += 1
                        progress.advance(migrate_task)
                        continue
                    
                    # Get product collections before migration
                    try:
                        source_collections = await source_client.get_product_collections(product["id"])
                        log.info(f"Found {len(source_collections)} collections for product '{product.get('title')}'")
                    except Exception as e:
                        log.warning(f"Failed to fetch collections for product '{product.get('title')}': {str(e)}")
                        source_collections = []
                    
                    existing_product = await dest_client.get_product_by_sku(sku)
                    migrated_product = None
                    
                    if existing_product:
                        try:
                            # Update existing product
                            migrated_product = await dest_client.update_product(existing_product["id"], product)
                            log.info(f"Updated product '{product.get('title')}' with SKU '{sku}'")
                            updated_count += 1
                        except Exception as e:
                            log.error(f"Failed to update product '{product.get('title')}' with SKU '{sku}': {str(e)}")
                            error_count += 1
                    else:
                        try:
                            # Create new product
                            migrated_product = await dest_client.create_product(product)
                            log.info(f"Created product '{product.get('title')}' with SKU '{sku}'")
                            created_count += 1
                        except Exception as e:
                            log.error(f"Failed to create product '{product.get('title')}' with SKU '{sku}': {str(e)}")
                            error_count += 1
                    
                    # Store collection information for later processing
                    if migrated_product and source_collections:
                        product_collections[migrated_product["id"]] = source_collections
                    
                    progress.advance(migrate_task)
                
                except Exception as e:
                    error_count += 1
                    log.error(f"Error processing product '{product.get('title', 'Unknown')}': {str(e)}")
                    progress.advance(migrate_task)
            
            # Process collections after all products are migrated
            if product_collections:
                log.info("Starting collection migration process")
                collection_task = progress.add_task(
                    "Migrating collections...",
                    total=sum(len(cols) for cols in product_collections.values())
                )
                
                for product_id, collections in product_collections.items():
                    for collection in collections:
                        try:
                            # Check if collection exists in destination store
                            dest_collection = await dest_client.get_collection_by_title(collection["title"])
                            
                            if not dest_collection:
                                # Create new collection
                                collection_data = {
                                    "title": collection["title"],
                                    "body_html": collection.get("body_html", ""),
                                    "published": collection.get("published", True)
                                }
                                try:
                                    dest_collection = await dest_client.create_collection(collection_data)
                                    log.info(f"Created collection '{collection['title']}'")
                                except Exception as e:
                                    log.error(f"Failed to create collection '{collection['title']}': {str(e)}")
                                    progress.advance(collection_task)
                                    continue
                            
                            # Add product to collection
                            try:
                                await dest_client.add_product_to_collection(product_id, dest_collection["id"])
                                log.info(f"Added product {product_id} to collection '{collection['title']}'")
                                collection_count += 1
                            except Exception as e:
                                log.error(f"Failed to add product {product_id} to collection '{collection['title']}': {str(e)}")
                            
                            progress.advance(collection_task)
                            
                        except Exception as e:
                            log.error(f"Error processing collection '{collection.get('title', 'Unknown')}' for product {product_id}: {str(e)}")
                            error_count += 1
                            progress.advance(collection_task)
        
        # Log final statistics
        log.info("Migration completed!")
        log.info(f"Total products processed: {total_products}")
        log.info(f"Products created: {created_count}")
        log.info(f"Products updated: {updated_count}")
        log.info(f"Products skipped: {skipped_count}")
        log.info(f"Collection assignments: {collection_count}")
        if error_count > 0:
            log.warning(f"Items with errors: {error_count}")
            
    except Exception as e:
        log.error(f"Migration failed: {str(e)}")
        raise

async def validate_store_credentials(store_url: str, admin_key: str) -> bool:
    """Validate store credentials by creating a test client."""
    try:
        client = ShopifyClient(store_url, admin_key)
        return await client.validate_credentials()
    except Exception as e:
        log.error(f"Error validating credentials for {store_url}: {str(e)}")
        return False

async def main():
    """Main function to run the migration process."""
    try:
        log.info("Loading environment variables")
        load_dotenv()
        
        required_env_vars = [
            "SOURCE_SHOPIFY_STORE",
            "SOURCE_ADMIN_KEY",
            "DESTINATION_SHOPIFY_STORE",
            "DESTINATION_ADMIN_KEY"
        ]
        
        # Check for required environment variables
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate source store credentials
        log.info("Validating source store credentials")
        source_valid = await validate_store_credentials(
            os.getenv("SOURCE_SHOPIFY_STORE"),
            os.getenv("SOURCE_ADMIN_KEY")
        )
        
        # Validate destination store credentials
        log.info("Validating destination store credentials")
        dest_valid = await validate_store_credentials(
            os.getenv("DESTINATION_SHOPIFY_STORE"),
            os.getenv("DESTINATION_ADMIN_KEY")
        )
        
        if not (source_valid and dest_valid):
            raise ValueError("Invalid credentials. Please check your Admin API access tokens.")
        
        # Initialize source and destination clients
        log.info("Initializing Shopify clients")
        source_client = ShopifyClient(
            store_url=os.getenv("SOURCE_SHOPIFY_STORE"),
            admin_key=os.getenv("SOURCE_ADMIN_KEY")
        )
        
        dest_client = ShopifyClient(
            store_url=os.getenv("DESTINATION_SHOPIFY_STORE"),
            admin_key=os.getenv("DESTINATION_ADMIN_KEY")
        )
        
        # Confirm before proceeding
        if Confirm.ask("Ready to start migration. Do you want to proceed?"):
            await migrate_products(source_client, dest_client)
        else:
            log.info("Migration cancelled by user")
        
    except Exception as e:
        log.error(f"Migration process failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
