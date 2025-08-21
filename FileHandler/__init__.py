import logging
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.communication.email import EmailClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="FileHandler")
@app.route(route="FileHandler", methods=["POST"])
def file_handler(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("File upload request received.")

    try:
        # File পড়া (curl দিয়ে পাঠানো multipart থেকে)
        file = req.files.get("file")
        if not file:
            return func.HttpResponse("No file uploaded!", status_code=400)

        file_name = file.filename
        file_data = file.stream.read()

        # Storage connection string from App Settings
        storage_conn_str = os.environ["AzureWebJobsStorage"]
        container_name = "upload"

        # Blob Upload
        blob_service = BlobServiceClient.from_connection_string(storage_conn_str)
        container_client = blob_service.get_container_client(container_name)
        container_client.upload_blob(name=file_name, data=file_data, overwrite=True)

        logging.info(f"File '{file_name}' uploaded to container '{container_name}'.")

        # Email Settings
        sender = "DoNotReply@ed606959-b263-4a31-b27e-090fcddddb2d.azurecomm.net"
        to_email = "faruk.cse.pust12@gmail.com"
        conn_str = "endpoint=https://my-email-service.asiapacific.communication.azure.com/;accesskey=2UnN2o8oy7QBfS2bnXzGRcqSNVOUDEOtqVCnUxNREve3oIrLCTITJQQJ99BHACULyCpSubbrAAAAAZCSMEoC"

        email_client = EmailClient.from_connection_string(conn_str)
        message = {
            "senderAddress": sender,
            "recipients": {"to": [{"address": to_email}]},
            "content": {
                "subject": f"File Uploaded: {file_name}",
                "plainText": f"File '{file_name}' uploaded successfully to container '{container_name}'."
            }
        }

        poller = email_client.begin_send(message)
        result = poller.result()

        logging.info(f"Email sent successfully! MessageId = {result['messageId']}")

        return func.HttpResponse(
            f"✅ File '{file_name}' uploaded & email sent to {to_email}!",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"❌ Failed. Error: {str(e)}",
            status_code=500
        )
