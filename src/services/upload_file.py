import cloudinary
import cloudinary.uploader


class UploadFileService:
    """
    Service for handling file uploads to Cloudinary.

    """

    def __init__(self, cloud_name, api_key, api_secret):
        """
        Initializes the UploadFileService with Cloudinary configuration.

        Args:
            cloud_name (str): The Cloudinary cloud name.
            api_key (str): The Cloudinary API key.
            api_secret (str): The Cloudinary API secret.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username) -> str:
        """
        Uploads a file to Cloudinary and returns the URL.

        Args:
            file: The file to upload.
            username (str): The username used to create a unique public ID.

        Returns:
            str: The URL of the uploaded image.
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
