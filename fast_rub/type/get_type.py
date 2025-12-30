import os


def get_file_category(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    ext = ext.lower().lstrip('.')
    if not ext:
        return "unknown"
    file_categories = {
        'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tif', 'psd'],
        'video': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'mpeg', 'mpg', '3gp', 'ts'],
        'audio': ['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma', 'm4a', 'aiff', 'mid', 'midi'],
        'voice': ['amr', '3ga'],
        'document': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'ppt', 'pptx', 'csv'],
        'web': ['html', 'htm', 'css', 'js', 'json', 'xml', 'php', 'asp', 'aspx'],
        'code': ['py', 'pyc', 'c', 'cpp', 'cs', 'java', 'rb', 'go', 'rs', 'swift', 'kt'],
        'archive': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'iso'],
        'executable': ['exe', 'dll', 'bat', 'sh']
    }
    for category, extensions in file_categories.items():
        if ext in extensions:
            return category
    return "other"

