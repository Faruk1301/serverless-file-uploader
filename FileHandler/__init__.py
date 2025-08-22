import logging
import traceback
from azure.storage.blob import BlobServiceClient
from azure.communication.email import EmailClient
import azure.functions as func
from requests_toolbelt.multipart import decoder


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="FileHandler")
@app.route(route="FileHandler", methods=["POST"])
def file_handler(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("📩 File upload request received")

    try:
        # --------------------------
        # Parse multipart/form-data safely
        # --------------------------
        content_type = req.headers.get("Content-Type")
        body = req.get_body()
        logging.info(f"Content-Type: {content_type}, Body length={len(body)}")

        multipart_data = decoder.MultipartDecoder(body, content_type)

        file_name = None
        file_data = None

        for part in multipart_data.parts:
            content_disposition = part.headers.get(b"Content-Disposition", b"").decode()
            if "filename=" in content_disposition:
                # Extract filename
                file_name = content_disposition.split("filename=")[1].strip('"')
                file_data = part.content
                break

        if not file_name or not file_data:
            return func.HttpResponse("❌ No file uploaded!", status_code=400)

        logging.info(f"Step 2️⃣ File '{file_name}' parsed successfully (size={len(file_data)} bytes)")

        # --------------------------
        # Blob Storage Upload
        # --------------------------
        logging.info("Step 3️⃣ Connecting to Blob Storage")
        storage_conn_str = (
            "DefaultEndpointsProtocol=https;"
            "AccountName=mystorageeastasia1301;"
            "AccountKey=IRvqGy4MhFymaZ7f9XmZNeADPoYyQGzTVZcTRTKZ3S04oaWLI3nyMOiFlcFJS26PmODFaaj1GX23+AStoSDhtA==;"
            "EndpointSuffix=core.windows.net"
        )
        container_name = "upload"

        blob_service = BlobServiceClient.from_connection_string(storage_conn_str)
        container_client = blob_service.get_container_client(container_name)

        try:
            container_client.create_container()
            logging.info(f"Container '{container_name}' created")
        except Exception:
            logging.info(f"Container '{container_name}' already exists")

        container_client.upload_blob(name=file_name, data=file_data, overwrite=True)
        logging.info(f"Step 4️⃣ File '{file_name}' uploaded to container '{container_name}'")

        # --------------------------
        # Send Email via ACS
        # --------------------------
        logging.info("Step 5️⃣ Sending email via ACS")
        conn_str = (
            "endpoint=https://my-email-service.asiapacific.communication.azure.com/;"
            "accesskey=2UnN2o8oy7QBfS2bnXzGRcqSNVOUDEOtqVCnUxNREve3oIrLCTITJQQJ99BHACULyCpSubbrAAAAAZCSMEoC"
        )
        sender = "DoNotReply@ed606959-b263-4a31-b27e-090fcddddb2d.azurecomm.net"
        to_email = "faruk.cse.pust12@gmail.com"

        email_client = EmailClient.from_connection_string(conn_str)

        message = {
            "senderAddress": sender,
            "recipients": {"to": [{"address": to_email}]},
            "content": {
                "subject": f"File Uploaded: {file_name}",
                "plainText": f"✅ File '{file_name}' uploaded successfully to container '{container_name}'."
            }
        }

        poller = email_client.begin_send(message)
        result = poller.result()

        logging.info(f"Step 6️⃣ Email send status: {result.status}, MessageId={result.message_id}")

        return func.HttpResponse(
            f"✅ File '{file_name}' uploaded & email sent to {to_email}",
            status_code=200
        )

    except Exception as e:
        error_details = traceback.format_exc()
        logging.error("❌ Error while processing:\n" + error_details)

        return func.HttpResponse(
            body=f"Error occurred: {str(e)}\n\nTraceback:\n{error_details}",
            status_code=500,
            mimetype="text/plain"
        )

