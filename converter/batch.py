import os
from pathlib import Path
from typing import List, Callable, Optional

import utils
from converter import load_image, process_single, save_image


def scan_folder(folder_path: str) -> List[str]:
    supported_extensions = utils.get_supported_extensions()
    image_files = []
    
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return []
    
    for ext in supported_extensions:
        image_files.extend(folder.glob(f"*{ext}"))
        image_files.extend(folder.glob(f"*{ext.upper()}"))
    
    unique_files = list(set(image_files))
    return [str(f) for f in unique_files]


def process_batch(input_folder: str, output_folder: str, target_format: str,
                  width: Optional[int] = None, height: Optional[int] = None,
                  keep_proportions: bool = False, interpolation: str = "LANCZOS",
                  quality: int = 95, progress_callback: Optional[Callable] = None) -> tuple:
    if not utils.ensure_directory_exists(output_folder):
        return 0, 0
    
    image_files = scan_folder(input_folder)
    if not image_files:
        return 0, 0
    
    success_count = 0
    error_count = 0
    total = len(image_files)
    
    for idx, input_path in enumerate(image_files):
        img = load_image(input_path)
        if img is None:
            error_count += 1
            if progress_callback:
                progress_callback(idx + 1, total, input_path, False)
            continue
        
        use_resize = (width is not None and height is not None and width > 0 and height > 0)
        if use_resize:
            processed_img = process_single(img, width, height, target_format, 
                                          keep_proportions, interpolation, quality)
        else:
            from converter import convert_format
            processed_img = convert_format(img, target_format, quality)
        
        if processed_img is None:
            error_count += 1
            if progress_callback:
                progress_callback(idx + 1, total, input_path, False)
            continue
        
        output_path = utils.create_output_path(input_path, target_format, output_folder)
        
        if save_image(processed_img, output_path, target_format, quality):
            success_count += 1
            if progress_callback:
                progress_callback(idx + 1, total, input_path, True)
        else:
            error_count += 1
            if progress_callback:
                progress_callback(idx + 1, total, input_path, False)
    
    return success_count, error_count