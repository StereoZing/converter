import os
from pathlib import Path


def validate_positive_integer(value: str) -> int or None:
    try:
        num = int(value)
        if num > 0:
            return num
    except ValueError:
        pass
    return None


def get_supported_extensions() -> list:
    return ['.png', '.jpg', '.jpeg', '.bmp', '.webp']


def create_output_path(input_path: str, target_format: str, output_dir: str = None) -> str:
    input_path_obj = Path(input_path)
    base_name = input_path_obj.stem
    
    ext_map = {
        'PNG': '.png',
        'JPEG': '.jpg',
        'BMP': '.bmp',
        'WEBP': '.webp'
    }
    extension = ext_map.get(target_format, '.png')
    
    output_filename = base_name + extension
    
    if output_dir:
        output_path = Path(output_dir) / output_filename
    else:
        output_path = input_path_obj.parent / output_filename
    
    return str(output_path)


def ensure_directory_exists(path: str) -> bool:
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False