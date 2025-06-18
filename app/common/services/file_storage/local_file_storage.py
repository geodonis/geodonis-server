import os
from typing import BinaryIO
from pathlib import Path
from datetime import datetime
import io


class LocalFileStorage:
    """
    This is a simple local file storage implementation for a transition to S3. It mimics the S3FileStorage class we will be using.
    """
    def __init__(self, base_path: str, base_url_path: str):
        self.base_path = base_path # os path to the parent folder for the upload folders/files
        self.base_url_path = base_url_path # The base of path for local protected file requests

    def get_file(self, folder_key: str, file_name: str) -> io.BytesIO:
        """
        Retrieve the content of a file from the local file system.
        """
        full_path = os.path.join(self.base_path, folder_key, file_name)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")
        
        with open(full_path, 'rb') as file:
            return io.BytesIO(file.read())

    def get_text_file(self, folder_key: str, file_name: str, encoding: str = 'utf-8') -> str:
        """
        Retrieve the content of a text file from the local file system as a string.
        """
        full_path = os.path.join(self.base_path, folder_key, file_name)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")
        
        with open(full_path, 'r', encoding=encoding) as file:
            return file.read()

    def generate_presigned_url(self, folder_key: str, file_name: str, expiration: int = 3600) -> str:
        # Construct a URL for the local protected file storage.
        # Note: This won't actually expire
        network_path = os.path.join(self.base_url_path, folder_key, file_name)
        network_file_path = Path(network_path).as_posix()
        return network_file_path

    def save_file_content(self, folder_key: str, file_name: str, file_content: str | bytes) -> bool:
        full_path = os.path.join(self.base_path, folder_key, file_name)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        mode = 'wb' if isinstance(file_content, bytes) else 'w'
        with open(full_path, mode) as f:
            f.write(file_content)

    def save_file_object(self, folder_key: str, file_name: str, file_object: BinaryIO) -> bool:
        full_path = os.path.join(self.base_path, folder_key, file_name)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(file_object.read())

    def save_files_content(self, folder_key: str, files: list[tuple]) -> bool:
        for file_name, file_content in files:
            self.save_file_content(folder_key, file_name, file_content)

    def save_files_objects(self, folder_key: str, files: list[tuple]) -> bool:
        for file_name, file_object in files:
            self.save_file_object(folder_key, file_name, file_object)

    def file_exists(self, folder_key: str, file_name: str) -> bool:
        full_path = os.path.join(self.base_path, folder_key, file_name)
        return os.path.exists(full_path)
    
    def delete_file(self, folder_key: str, file_name: str) -> bool:
        try:
            full_path = os.path.join(self.base_path, folder_key, file_name)
            if not os.path.exists(full_path):
                return False
            
            os.remove(full_path)
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def list_files(self, folder_key: str, include_subdirectories: bool = False) -> dict:
        try:
            full_path = os.path.join(self.base_path, folder_key)
            
            result_files = []

            if not os.path.exists(full_path):
                return result_files

            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                
                if os.path.isfile(item_path):
                    stats = os.stat(item_path)
                    result_files.append({
                        "name": item,
                        "size": stats.st_size,
                        "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
                    })
                elif os.path.isdir(item_path):                  
                    if include_subdirectories:
                        subdirectory_key = os.path.join(folder_key, item)
                        subdirectory_contents = self.list_files(subdirectory_key, include_subdirectories=True)
                        
                        for subfile in subdirectory_contents["files"]:
                            subfile["name"] = os.path.join(item, subfile["name"])
                            result_files.append(subfile)

            return result_files
        except Exception as e:
            print(f"An error occurred: {e}")
            return {"error": str(e)}