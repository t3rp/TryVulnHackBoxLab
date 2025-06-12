import os
import sys
import argparse
from PIL import Image
import ocrmypdf
from tqdm import tqdm

def fix_image_size(image):
    # Convert to RGB and return - no resizing at all
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Slight contrast enhancement for OCR only
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(1.1)

def create_pdf(folder, output_file):
    # Find image files
    image_files = []
    for file in os.listdir(folder):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_files.append(file)
    
    if not image_files:
        print("No images found!")
        return
    
    # Sort by number in filename
    def get_page_number(filename):
        numbers = ''.join(c for c in filename if c.isdigit())
        return int(numbers) if numbers else 0
    
    image_files.sort(key=get_page_number)
    
    print(f"Processing {len(image_files)} images...")
    
    # Process all images with progress bar
    processed_images = []
    for filename in tqdm(image_files, 
                        desc="Processing pages", 
                        unit="page", 
                        bar_format="{desc:<18} {bar} {percentage:3.0f}% {n_fmt}/{total_fmt} {elapsed}"):
        
        image_path = os.path.join(folder, filename)
        image = Image.open(image_path).convert('RGB')
        fixed_image = fix_image_size(image)
        processed_images.append(fixed_image)
    
    # Create PDF
    print("Creating PDF...")
    temp_pdf = "temp.pdf"
    first_page = processed_images[0]
    other_pages = processed_images[1:]
    first_page.save(temp_pdf, save_all=True, append_images=other_pages)
    
    # Add OCR to make searchable
    print("Adding OCR...")
    ocrmypdf.ocr(temp_pdf, output_file, deskew=True)
    
    # Clean up
    os.remove(temp_pdf)
    print(f"Done! Saved: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Convert images to searchable PDF')
    parser.add_argument('folder', help='Folder with images')
    parser.add_argument('-o', '--output', default='document.pdf', help='Output PDF name')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.folder):
        print(f"Folder not found: {args.folder}")
        sys.exit(1)
    
    create_pdf(args.folder, args.output)

if __name__ == "__main__":
    main()