from PIL import Image
import utils


def load_image(file_path: str) -> Image.Image or None:
    try:
        img = Image.open(file_path)
        return img
    except (IOError, OSError, Image.UnidentifiedImageError):
        return None


def resize_image(image: Image.Image, width: int, height: int, 
                 keep_proportions: bool = False, 
                 interpolation: str = "LANCZOS") -> Image.Image:
    if keep_proportions:
        new_image = image.copy()
        if interpolation == "BILINEAR":
            new_image.thumbnail((width, height), Image.BILINEAR)
        else:
            new_image.thumbnail((width, height), Image.LANCZOS)
        return new_image
    else:
        if interpolation == "BILINEAR":
            return image.resize((width, height), Image.BILINEAR)
        else:
            return image.resize((width, height), Image.LANCZOS)


def handle_transparency(image: Image.Image, target_format: str) -> Image.Image:
    if target_format.upper() in ['JPEG', 'BMP']:
        if image.mode in ('RGBA', 'LA', 'P') and 'transparency' in image.info:
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            return background
        elif image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            return background
        elif image.mode != 'RGB':
            return image.convert('RGB')
    return image


def convert_format(image: Image.Image, target_format: str, quality: int = 95) -> Image.Image:
    image = handle_transparency(image, target_format)
    
    if target_format.upper() == 'JPEG' and image.mode not in ('RGB', 'L'):
        image = image.convert('RGB')
    elif target_format.upper() == 'BMP' and image.mode != 'RGB':
        image = image.convert('RGB')
    elif target_format.upper() == 'PNG' and image.mode not in ('RGBA', 'RGB', 'L'):
        image = image.convert('RGBA')
    
    return image


def save_image(image: Image.Image, output_path: str, target_format: str, quality: int = 95) -> bool:
    try:
        params = {}
        if target_format.upper() in ['JPEG', 'WEBP']:
            params['quality'] = quality
            params['optimize'] = True
        
        if target_format.upper() == 'PNG':
            params['compress_level'] = 6
        
        image.save(output_path, format=target_format.upper(), **params)
        return True
    except (IOError, OSError):
        return False


def process_single(image: Image.Image, width: int, height: int, 
                   target_format: str, keep_proportions: bool = False,
                   interpolation: str = "LANCZOS", quality: int = 95) -> Image.Image or None:
    try:
        resized = resize_image(image, width, height, keep_proportions, interpolation)
        
        converted = convert_format(resized, target_format, quality)
        
        return converted
    except Exception:
        return None