import os
import sys
import argparse
from PIL import Image
import ocrmypdf

def normalize_image(image, target_width=None, target_height=None):
    """Normalize image size and aspect ratio to prevent skewing"""
    if target_width is None or target_height is None:
        # Use A4 proportions as default (210:297 ratio)
        target_width = 2100
        target_height = 2970
    
    # Calculate aspect ratios
    original_ratio = image.width / image.height
    target_ratio = target_width / target_height
    
    if original_ratio > target_ratio:
        # Image is wider than target, fit by width
        new_width = target_width
        new_height = int(target_width / original_ratio)
    else:
        # Image is taller than target, fit by height
        new_height = target_height
        new_width = int(target_height * original_ratio)
    
    # Resize image maintaining aspect ratio
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create a white background with target dimensions
    background = Image.new('RGB', (target_width, target_height), 'white')
    
    # Calculate position to center the image
    x = (target_width - new_width) // 2
    y = (target_height - new_height) // 2
    
    # Paste the resized image onto the background
    background.paste(resized_image, (x, y))
    
    return background

def images_to_pdf(image_folder, output_pdf):
    # Support multiple image formats
    image_extensions = {'.jpeg', '.jpg', '.png', '.bmp', '.tiff', '.webp'}
    files = [f for f in os.listdir(image_folder) 
             if os.path.splitext(f.lower())[1] in image_extensions]
    
    # Sort numerically by filename
    files = sorted(files, key=lambda f: int(''.join(filter(str.isdigit, os.path.splitext(f)[0])) or '0'))

    if not files:
        print(f"No image files found in folder: {image_folder}")
        return

    print(f"Found {len(files)} images to process...")
    
    # Process first image to get target dimensions
    first_image_path = os.path.join(image_folder, files[0])
    first_image = Image.open(first_image_path).convert("RGB")
    
    # Normalize first image
    normalized_first = normalize_image(first_image)
    target_width, target_height = normalized_first.size
    
    print(f"Normalizing images to {target_width}x{target_height}...")
    
    # Process remaining images
    image_list = []
    for i, filename in enumerate(files[1:], 2):
        print(f"Processing image {i}/{len(files)}: {filename}")
        image_path = os.path.join(image_folder, filename)
        image = Image.open(image_path).convert("RGB")
        normalized_image = normalize_image(image, target_width, target_height)
        image_list.append(normalized_image)

    # Save images as a non-searchable PDF first
    temp_pdf = "temp_output.pdf"
    print("Creating PDF...")
    normalized_first.save(temp_pdf, save_all=True, append_images=image_list)

    # Apply OCR to make the PDF searchable
    print("Applying OCR...")
    ocrmypdf.ocr(temp_pdf, output_pdf, deskew=True)

    # Remove temp file
    os.remove(temp_pdf)

    print(f"Searchable PDF saved as: {output_pdf}")

def main():
    parser = argparse.ArgumentParser(description='Convert images to searchable PDF')
    parser.add_argument('folder', nargs='?', default='.', 
                       help='Folder containing images (default: current directory)')
    parser.add_argument('-o', '--output', default='writeup.pdf',
                       help='Output PDF filename (default: writeup.pdf)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.folder):
        print(f"Error: '{args.folder}' is not a valid directory")
        sys.exit(1)
    
    images_to_pdf(args.folder, args.output)

if __name__ == "__main__":
    main()