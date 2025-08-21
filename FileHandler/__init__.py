import logging
from io import BytesIO
import azure.functions as func

from azure.storage.blob import BlobServiceClient
from azure.communication.email import EmailClient
import werkzeug
from werkzeug.datastructures import FileStorage


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="FileHandler")
@app.route(route="FileHandler", methods=["POST"])
def file_handler(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("📩 File upload request received")

    try:
        # --------------------------
        # Parse multipart/form-data
        # --------------------------
        content_type = req.headers.get("Content-Type")
        body = req.get_body()

        environ = {
            "wsgi.input": BytesIO(body),
            "CONTENT_LENGTH": len(body),
            "CONTENT_TYPE": content_type,
            "REQUEST_METHOD": "POST"
        }

        files = werkzeug.formparser.parse_form_data(environ)[1]
        if "file" not in files:
            return func.HttpResponse("❌ No file uploaded!", status_code=400)

        file: FileStorage = files["file"]
        file_name = file.filename
        file_data = file.stream.read()

        # --------------------------
        # Blob Storage Upload
        # --------------------------
        storage_conn_str = (
            "DefaultEndpointsProtocol=https;"
            "EndpointSuffix=core.windows.net;"
            "AccountName=mystorageeastasia1301;"
            "AccountKey=IRvqGy4MhFymaZ7f9XmZNeADPoYyQGzTVZcTRTKZ3S04oaWLI3nyMOiFlcFJS26PmODFaaj1GX23+AStoSDhtA==;"
            "BlobEndpoint=https://mystorageeastasia1301.blob.core.windows.net/;"
            "FileEndpoint=https://mystorageeastasia1301.file.core.windows.net/;"
            "QueueEndpoint=https://mystorageeastasia1301.queue.core.windows.net/;"
            "TableEndpoint=https://mystorageeastasia1301.table.core.windows.net/"
        )

        container_name = "upload"
        blob_service = BlobServiceClient.from_connection_string(storage_conn_str)
        container_client = blob_service.get_container_client(container_name)
        container_client.upload_blob(name=file_name, data=file_data, overwrite=True)

        logging.info(f"✅ File '{file_name}' uploaded to container '{container_name}'")

        # --------------------------
        # Send Email via ACS
        # --------------------------
        conn_str = "endpoint=https://my-email-service.asiapacific.communication.azure.com/;accesskey=2UnN2o8oy7QBfS2bnXzGRcqSNVOUDEOtqVCnUxNREve3oIrLCTITJQQJ99BHACULyCpSubbrAAAAAZCSMEoC"
        sender = "DoNotReply@ed606959-b263-4a31-b27e-090fcddddb2d.azurecomm.net"
        to_email = "faruk.cse.pust12@gmail.com"

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

        logging.info(f"📧 Email send status: {result.status}")
        logging.info(f"📨 Message Id: {result.message_id}")

        return func.HttpResponse(
            f"✅ File '{file_name}' uploaded & email sent to {to_email}",
            status_code=200
        )

    except Exception as e:
        logging.error("❌ Error while processing", exc_info=True)
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

