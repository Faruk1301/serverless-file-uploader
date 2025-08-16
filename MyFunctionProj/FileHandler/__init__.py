import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import os

connect_str = os.getenv("AzureWebJobsStorage")
container_name = "uploads"

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("File upload function triggered.")

    try:
        # POST request এ ফাইল নাও
        if req.method == "POST":
            file = req.files['file']
            filename = file.filename

            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            container_client = blob_service_client.get_container_client(container_name)

            try:
                container_client.create_container()
            except Exception:
                pass

            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(file.stream, overwrite=True)

            # সব ফাইল লিস্ট করো
            blobs = [b.name for b in container_client.list_blobs()]

            return func.HttpResponse(
                body=str({
                    "message": "File uploaded successfully!",
                    "uploaded_file": filename,
                    "files_in_storage": blobs
                }),
                status_code=200,
                mimetype="application/json"
            )

        # GET request এ লিস্ট দেখাও
        elif req.method == "GET":
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            container_client = blob_service_client.get_container_client(container_name)
            blobs = [b.name for b in container_client.list_blobs()]

            return func.HttpResponse(
                body=str({"files_in_storage": blobs}),
                status_code=200,
                mimetype="application/json"
            )

        else:
            return func.HttpResponse("Method not allowed", status_code=405)

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            body=str({"error": str(e)}),
            status_code=500
        )
