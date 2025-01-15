import pytest
from unittest.mock import Mock, patch, AsyncMock
from shopify_migration.shopify_client import ShopifyClient

@pytest.fixture
def mock_client():
    return ShopifyClient(
        store_url="test-store.myshopify.com",
        admin_key="test_admin_token"
    )

@pytest.fixture
def sample_product():
    return {
        "id": 1,
        "title": "Test Product",
        "body_html": "<p>Test description</p>",
        "vendor": "Test Vendor",
        "product_type": "Test Type",
        "handle": "test-product",
        "status": "active",
        "variants": [
            {
                "id": 1,
                "product_id": 1,
                "sku": "TEST-SKU-1",
                "price": "10.00",
                "inventory_quantity": 10
            },
            {
                "id": 2,
                "product_id": 1,
                "sku": "TEST-SKU-2",
                "price": "15.00",
                "inventory_quantity": 5
            }
        ],
        "images": [
            {
                "id": 1,
                "src": "https://test.com/image1.jpg",
                "alt": "Test Image 1",
                "position": 1
            },
            {
                "id": 2,
                "src": "https://test.com/image2.jpg",
                "alt": "Test Image 2",
                "position": 2
            }
        ],
        "options": [
            {
                "name": "Size",
                "values": ["Small", "Medium", "Large"]
            }
        ]
    }

@pytest.mark.asyncio
async def test_get_products(mock_client, sample_product):
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock the validation request
        mock_validation = AsyncMock()
        mock_validation.status_code = 200
        mock_validation.raise_for_status.return_value = None
        mock_validation.json.return_value = {"shop": {"id": 1}}
        
        # Mock the products request
        mock_products = AsyncMock()
        mock_products.status_code = 200
        mock_products.raise_for_status.return_value = None
        mock_products.json.return_value = {"products": [sample_product]}
        
        # Set up the mock to return different responses for different URLs
        def mock_get_side_effect(*args, **kwargs):
            if args[0].endswith('/shop.json'):
                return mock_validation
            return mock_products
        
        mock_get.side_effect = mock_get_side_effect
        
        products = await mock_client.get_products()
        assert len(products) == 1
        product = products[0]
        assert product["title"] == "Test Product"
        assert len(product["variants"]) == 2
        assert len(product["images"]) == 2
        assert product["variants"][0]["sku"] == "TEST-SKU-1"
        assert product["images"][0]["alt"] == "Test Image 1"
        
        # Verify headers were sent correctly
        headers_calls = [call.kwargs.get('headers') for call in mock_get.call_args_list]
        for headers in headers_calls:
            assert headers["X-Shopify-Access-Token"] == "test_admin_token"
            assert headers["Content-Type"] == "application/json"

@pytest.mark.asyncio
async def test_create_product(mock_client, sample_product):
    with patch('httpx.AsyncClient.get') as mock_get, \
         patch('httpx.AsyncClient.post') as mock_post:
        # Mock the validation request
        mock_validation = AsyncMock()
        mock_validation.status_code = 200
        mock_validation.raise_for_status.return_value = None
        mock_validation.json.return_value = {"shop": {"id": 1}}
        mock_get.return_value = mock_validation
        
        # Mock the create request
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"product": sample_product}
        mock_post.return_value = mock_response
        
        response = await mock_client.create_product(sample_product)
        
        # Verify the cleaned data was sent
        sent_data = mock_post.call_args.kwargs['json']['product']
        assert "id" not in sent_data
        assert len(sent_data["variants"]) == 2
        assert "product_id" not in sent_data["variants"][0]
        assert len(sent_data["images"]) == 2
        assert "id" not in sent_data["images"][0]
        
        # Verify headers were sent correctly
        assert mock_post.call_args.kwargs['headers'] == mock_client.headers

@pytest.mark.asyncio
async def test_update_product(mock_client, sample_product):
    with patch('httpx.AsyncClient.get') as mock_get, \
         patch('httpx.AsyncClient.put') as mock_put:
        # Mock the validation request
        mock_validation = AsyncMock()
        mock_validation.status_code = 200
        mock_validation.raise_for_status.return_value = None
        mock_validation.json.return_value = {"shop": {"id": 1}}
        mock_get.return_value = mock_validation
        
        # Mock the update request
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"product": sample_product}
        mock_put.return_value = mock_response
        
        response = await mock_client.update_product(1, sample_product)
        
        # Verify the cleaned data was sent
        sent_data = mock_put.call_args.kwargs['json']['product']
        assert "id" not in sent_data
        assert len(sent_data["variants"]) == 2
        assert "product_id" not in sent_data["variants"][0]
        assert len(sent_data["images"]) == 2
        assert "id" not in sent_data["images"][0]
        
        # Verify headers were sent correctly
        assert mock_put.call_args.kwargs['headers'] == mock_client.headers

@pytest.mark.asyncio
async def test_get_product_by_sku(mock_client, sample_product):
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock the validation request
        mock_validation = AsyncMock()
        mock_validation.status_code = 200
        mock_validation.raise_for_status.return_value = None
        mock_validation.json.return_value = {"shop": {"id": 1}}
        
        # Mock the products request
        mock_products = AsyncMock()
        mock_products.status_code = 200
        mock_products.raise_for_status.return_value = None
        mock_products.json.return_value = {"products": [sample_product]}
        
        # Set up the mock to return different responses for different URLs
        def mock_get_side_effect(*args, **kwargs):
            if args[0].endswith('/shop.json'):
                return mock_validation
            return mock_products
        
        mock_get.side_effect = mock_get_side_effect
        
        # Test finding first variant
        product = await mock_client.get_product_by_sku("TEST-SKU-1")
        assert product is not None
        assert product["title"] == "Test Product"
        
        # Test finding second variant
        product = await mock_client.get_product_by_sku("TEST-SKU-2")
        assert product is not None
        assert product["title"] == "Test Product"
        
        # Test non-existent SKU
        product = await mock_client.get_product_by_sku("NON-EXISTENT")
        assert product is None
        
        # Verify headers were sent correctly
        headers_calls = [call.kwargs.get('headers') for call in mock_get.call_args_list]
        for headers in headers_calls:
            assert headers["X-Shopify-Access-Token"] == "test_admin_token"
            assert headers["Content-Type"] == "application/json" 