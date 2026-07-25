def get_file_category(
    filename: str | None
) -> str | None:
    if not filename:
        return None
    file_categories = {
        'Image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tif', 'psd'],
        'Video': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'mpeg', 'mpg', '3gp', 'ts'],
        'Music': ['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma', 'm4a', 'aiff', 'mid', 'midi'],
        'Voice': ['ogg']
    }
    for category, extensions in file_categories.items():
        if filename in extensions:
            return category
    return "other"

