import boto3
from botocore.exceptions import ClientError
from typing import BinaryIO
import io

class S3FileStorage:
    def __init__(self, bucket_name: str, read_access_key: str, read_secret_key: str, 
                 write_access_key: str, write_secret_key: str):
        self.bucket_name = bucket_name
        self.s3_read = boto3.client('s3', 
                                    aws_access_key_id=read_access_key,
                                    aws_secret_access_key=read_secret_key)
        self.s3_write = boto3.client('s3', 
                                     aws_access_key_id=write_access_key,
                                     aws_secret_access_key=write_secret_key)

    def get_file(self, folder_key: str, file_name: str) -> io.BytesIO:
        """
        Retrieve the content of a file from S3.
        """
        file_key = f"{folder_key}/{file_name}"
        try:
            response = self.s3_read.get_object(Bucket=self.bucket_name, Key=file_key)
            file_content = io.BytesIO(response['Body'].read())
            # content_type = response.get('ContentType', 'application/octet-stream')
            # file_size = response.get('ContentLength', 0)
            return file_content
        except ClientError as e:
            print(f"Error retrieving file {file_key}: {e}")
            raise

    def get_text_file(self, folder_key: str, file_name: str, encoding: str = 'utf-8') -> str:
        """
        Retrieve the content of a text file from S3 as a string.
        """
        file_content, content_type, _ = self.get_file(folder_key, file_name)
        if not content_type.startswith('text/'):
            raise ValueError(f"File {file_name} is not a text file (content type: {content_type})")
        return file_content.getvalue().decode(encoding)

    def generate_presigned_url(self, folder_key: str, file_name: str, expiration: int = 3600) -> str:
        file_key = f"{folder_key}/{file_name}"
        url = self.s3_read.generate_presigned_url('get_object',
                                                  Params={'Bucket': self.bucket_name,
                                                          'Key': file_key},
                                                  ExpiresIn=expiration)
        return url

    def save_file_content(self, folder_key: str, file_name: str, file_content: str | bytes) -> bool:
        file_key = f"{folder_key}/{file_name}"
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')
        self.s3_write.put_object(Body=file_content, Bucket=self.bucket_name, Key=file_key)

    def save_file_object(self, folder_key: str, file_name: str, file_object: BinaryIO) -> bool:
        file_key = f"{folder_key}/{file_name}"
        self.s3_write.upload_fileobj(file_object, self.bucket_name, file_key)

    def save_files_content(self, folder_key: str, files: list[tuple]) -> bool:
        for file_name, file_content in files:
            self.save_file_content(folder_key, file_name, file_content)

    def save_files_objects(self, folder_key: str, files: list[tuple]) -> bool:
        for file_name, file_object in files:
            self.save_file_object(folder_key, file_name, file_object)

    def file_exists(self, folder_key: str, file_name: str) -> bool:
        try:
            file_key = f"{folder_key}/{file_name}"
            self.s3_read.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError:
            return False
        
    def delete_file(self, folder_key: str, file_name: str) -> bool:
        try:
            file_key = f"{folder_key}/{file_name}"
            self.s3_write.delete_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError as e:
            print(f"Error deleting file {file_key}: {e}")
            return False

    def list_files(self, folder_key: str, include_subdirectories: bool = False) -> dict:
        try:
            # Ensure folder_key ends with a slash if it's not empty
            if folder_key and not folder_key.endswith('/'):
                folder_key += '/'

            # List objects in the specified folder
            response = self.s3_read.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=folder_key,
                Delimiter='/' if not include_subdirectories else None
            )

            result_files = []

            # Process the contents
            if 'Contents' in response:
                for item in response['Contents']:
                    key = item['Key']
                    if key != folder_key:  # Exclude the folder itself
                        file_name = key.split('/')[-1]
                        if file_name:  # Ensure it's not an empty string (which could happen for nested directories)
                            result_files.append({
                                "name": file_name,
                                "size": item['Size'],
                                "last_modified": item['LastModified'].isoformat()
                            })

            return result_files
        except ClientError as e:
            print(f"An error occurred: {e}")
            return {"error": str(e)}
