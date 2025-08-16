import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import os
import json
import magic

# Environment variables
BLOB_CONNECTION_STRING = os.getenv("AzureWebJobsStorage")
STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "uploads")
MAX_FILE_SIZE_MB = 5
ALLOWED_TYPES = ["text/plain", "image/png", "image/jpeg"]

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing FileHandler request.")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        # Create container if not exists
        try:
            container_client.create_container()
        except Exception:
            pass

        if req.method == "POST":
            file = req.files.get("file")
            if not file:
                return func.HttpResponse(json.dumps({"error": "No file uploaded"}), status_code=400)

            # File size check
            file.seek(0,2)
            size_mb = file.tell() / (1024*1024)
            file.seek(0)
            if size_mb > MAX_FILE_SIZE_MB:
                return func.HttpResponse(json.dumps({"error": f"File too large, max {MAX_FILE_SIZE_MB} MB"}), status_code=400)

            # File type check
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)
            if mime_type not in ALLOWED_TYPES:
                return func.HttpResponse(json.dumps({"error": f"Unsupported file type: {mime_type}"}), status_code=400)

            filename = file.filename
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(file.read(), overwrite=True)
            blob_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{filename}"

            logging.info(f"File uploaded: {filename}")
            return func.HttpResponse(json.dumps({"message": "File uploaded", "filename": filename, "url": blob_url}), status_code=200)

        elif req.method == "GET":
            blob_list = container_client.list_blobs()
            files = [{"name": blob.name, "url": f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{blob.name}"} for blob in blob_list]
            return func.HttpResponse(json.dumps({"files": files}, indent=2), status_code=200)

        else:
            return func.HttpResponse(json.dumps({"error": "Method not allowed"}), status_code=405)

    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=500)
