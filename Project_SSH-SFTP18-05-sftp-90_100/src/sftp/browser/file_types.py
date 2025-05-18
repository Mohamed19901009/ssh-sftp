import os

class FileTypeManager:
    def __init__(self):
        self.file_icons = {
            'default': '📄',
            'directory': '📂',  # Changed to open folder icon
            'image': '🖼️',
            'video': '🎥',
            'audio': '🎵',
            'document': '📝',
            'archive': '📦',
            'code': '💻',
            'executable': '⚙️',
            'link': '🔗',
            'config': '⚙️',  # Added config file type
            'database': '🗄️'  # Added database file type
        }
        
        self.extension_types = {
            # Images
            'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image', 'bmp': 'image', 'svg': 'image', 'ico': 'image',
            # Videos
            'mp4': 'video', 'avi': 'video', 'mkv': 'video', 'mov': 'video', 'wmv': 'video', 'flv': 'video',
            # Audio
            'mp3': 'audio', 'wav': 'audio', 'flac': 'audio', 'm4a': 'audio', 'ogg': 'audio', 'aac': 'audio',
            # Documents
            'pdf': 'document', 'doc': 'document', 'docx': 'document', 'txt': 'document',
            'odt': 'document', 'rtf': 'document', 'md': 'document', 'csv': 'document',
            # Archives
            'zip': 'archive', 'rar': 'archive', '7z': 'archive', 'tar': 'archive', 'gz': 'archive', 'bz2': 'archive',
            # Code
            'py': 'code', 'java': 'code', 'cpp': 'code', 'h': 'code', 'js': 'code', 'html': 'code',
            'css': 'code', 'php': 'code', 'rb': 'code', 'go': 'code', 'rs': 'code', 'tsx': 'code', 'jsx': 'code',
            # Executables
            'exe': 'executable', 'msi': 'executable', 'app': 'executable', 'sh': 'executable',
            'bat': 'executable', 'cmd': 'executable',
            # Config files
            'json': 'config', 'yml': 'config', 'yaml': 'config', 'ini': 'config', 'conf': 'config', 'xml': 'config',
            # Database
            'db': 'database', 'sqlite': 'database', 'sqlite3': 'database'
        }
        
        self.type_colors = {
            'directory': '#2980B9',  # Bright Blue
            'image': '#27AE60',      # Emerald Green
            'video': '#E74C3C',      # Bright Red
            'audio': '#F1C40F',      # Bright Yellow
            'document': '#9B59B6',   # Bright Purple
            'archive': '#E67E22',    # Bright Orange
            'code': '#2ECC71',       # Bright Green
            'executable': '#D35400',  # Dark Orange
            'link': '#95A5A6',       # Silver
            'config': '#3498DB',     # Light Blue
            'database': '#1ABC9C',   # Turquoise
            'default': '#34495E'     # Dark Gray
        }

    def get_file_type(self, filename):
        if os.path.islink(filename):
            return 'link'
        if os.path.isdir(filename):
            return 'directory'
        
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        return self.extension_types.get(ext, 'default')

    def get_file_icon_and_color(self, filename, is_dir=False):
        if is_dir:
            return self.file_icons['directory'], self.type_colors['directory']
        
        file_type = self.get_file_type(filename)
        return self.file_icons.get(file_type, self.file_icons['default']), self.type_colors.get(file_type, self.type_colors['default'])