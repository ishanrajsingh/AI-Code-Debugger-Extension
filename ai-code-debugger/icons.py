from PIL import Image, ImageDraw, ImageFont

sizes = [16, 48, 128]
for size in sizes:
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw magnifying glass emoji representation
    center = size // 2
    draw.ellipse([size//4, size//4, 3*size//4, 3*size//4], 
                 fill='white', outline='#764ba2', width=max(2, size//32))
    
    img.save(f'extension/icons/icon{size}.png')
