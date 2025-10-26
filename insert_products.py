import os
import django
import random
from django.core.files import File

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AmazonProject.settings")
django.setup()

from products.models import Product

# Path to your products folder
folder_path = os.path.join(os.getcwd(), 'media', 'products')

# Get all .jpg files in the folder
image_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')]

if not image_files:
    print("No images found in the products folder.")
else:
    for filename in image_files:
        image_path = os.path.join(folder_path, filename)
        if not os.path.exists(image_path):
            print(f"File {filename} does not exist")
            continue

        # Check if a product with this filename already exists
        existing_product = Product.objects.filter(file=f'products/{filename}').first()
        if existing_product:
            print(f"Product {filename} already exists, skipping...")
            continue

        # Create new product
        with open(image_path, 'rb') as f:
            product = Product()
            product.price = round(random.uniform(10, 100), 2)
            product.is_active = True
            # Save file immediately
            product.file.save(filename, File(f), save=True)

        print(f"Added {filename} with price {product.price}")
