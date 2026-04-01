"""Validation exceptions."""


class ValidationError(Exception):
    """Base validation error."""
    pass


class FileSizeError(ValidationError):
    """Error for files exceeding size limit."""
    def __init__(self, file_path: str, size_mb: float, limit_mb: float):
        self.file_path = file_path
        self.size_mb = size_mb
        self.limit_mb = limit_mb
        super().__init__(
            f"File {file_path} is {size_mb:.1f}MB, which exceeds the limit of {limit_mb}MB"
        )


class TokenDetectedError(ValidationError):
    """Error when API tokens are detected in files."""
    def __init__(self, file_path: str, token_type: str, line_num: int | None = None):
        self.file_path = file_path
        self.token_type = token_type
        self.line_num = line_num
        location = f" at line {line_num}" if line_num else ""
        super().__init__(
            f"Potential {token_type} token detected in {file_path}{location}. "
            "Please remove or replace with environment variable."
        )


class DotFolderError(ValidationError):
    """Error when dot folders are detected that should be in .gitignore."""
    def __init__(self, dot_folders: list[str]):
        self.dot_folders = dot_folders
        super().__init__(
            f"Dot folders/files detected that should be in .gitignore: {', '.join(dot_folders)}"
        )
