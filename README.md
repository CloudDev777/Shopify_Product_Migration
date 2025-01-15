# Shopify Product Migration Tool

A Python tool for migrating products between Shopify stores, including variants, images, and collections. Built with async support for better performance.

## Features

- Full product data migration including variants, images, and metadata
- Preserves SKUs and intelligently updates existing products
- Handles image alt text and collection associations
- Asynchronous operations for improved performance
- Progress tracking and detailed logging
- Validation of store credentials and data integrity

## Requirements

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- Shopify Admin API access for both source and destination stores
- Source products must have valid and unique SKU values

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/shopify-product-migration.git
cd shopify-product-migration
```

2. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Copy `.env.sample` to `.env` and configure your Shopify credentials:
```bash
cp .env.sample .env
```

4. Install dependencies:
```bash
make install
```

## Configuration

### Prerequisites

1. **SKU Requirements**:
   - Every product in the source store MUST have a valid and unique SKU
   - SKUs are used as the primary identifier to match products between stores
   - Products without SKUs or with duplicate SKUs will be skipped during migration
   - Ensure all your products have SKUs assigned before starting the migration

### Shopify API Setup

1. Create private apps for both source and destination stores:
   - Go to your Shopify admin panel
   - Navigate to Settings > Apps and sales channels > Develop apps
   - Click "Create an app"
   - Set up the required permissions:
     - Products: Read and write
     - Collections: Read and write
     - Inventory: Read and write

2. Configure your `.env` file with the following credentials:
```env
SOURCE_SHOPIFY_STORE=source-store.myshopify.com
DESTINATION_SHOPIFY_STORE=destination-store.myshopify.com
SOURCE_ADMIN_KEY=your_source_admin_api_access_token
DESTINATION_ADMIN_KEY=your_destination_admin_api_access_token
```

## Usage

### Basic Usage

1. Run tests to ensure everything is set up correctly:
```bash
make test
```

2. Start the migration:
```bash
make migrate
```

### Advanced Usage

You can also use the package programmatically in your Python code:

```python
import asyncio
from shopify_migration import ShopifyClient, migrate_products

async def main():
    # Initialize clients
    source_client = ShopifyClient(
        store_url="source-store.myshopify.com",
        admin_key="your_source_admin_key"
    )
    
    dest_client = ShopifyClient(
        store_url="destination-store.myshopify.com",
        admin_key="your_destination_admin_key"
    )
    
    # Start migration
    await migrate_products(source_client, dest_client)

if __name__ == "__main__":
    asyncio.run(main())
```

## Migration Process

1. **Validation**: The tool first validates the credentials for both stores.
2. **Product Retrieval**: Fetches all products from the source store.
3. **SKU Matching**: For each product:
   - Checks if a product with the same SKU exists in the destination store
   - Updates existing products or creates new ones as needed
4. **Collection Migration**: After products are migrated:
   - Retrieves collection associations from the source store
   - Creates missing collections in the destination store
   - Associates products with their collections

## Error Handling

- The tool includes comprehensive error handling and logging
- Failed operations are logged with detailed error messages
- Progress is tracked and displayed in real-time
- The migration can be safely interrupted and resumed

## Development

### Running Tests

```bash
make test
```

### Clean Build Files

```bash
make clean
```

## Dependencies

Key dependencies used in this project:

- [httpx](https://www.python-httpx.org/) - Async HTTP client
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variable management
- [rich](https://rich.readthedocs.io/) - Terminal formatting and progress display

## Documentation References

- [Shopify Admin API Reference](https://shopify.dev/api/admin-rest)
- [Shopify Admin API: Products](https://shopify.dev/api/admin-rest/2024-01/resources/product)
- [Shopify Admin API: Collections](https://shopify.dev/api/admin-rest/2024-01/resources/collection)
- [uv Documentation](https://github.com/astral-sh/uv)
- [httpx Documentation](https://www.python-httpx.org/)
- [rich Documentation](https://rich.readthedocs.io/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions:
1. Check the [issue tracker](https://github.com/yourusername/shopify-product-migration/issues)
2. Create a new issue with a detailed description of your problem
