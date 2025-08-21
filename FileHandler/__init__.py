import logging
import os
import azure.functions as func
from azure.communication.email import EmailClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="SendEmail")
@app.route(route="sendemail", methods=["POST"])
def send_email(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger function received a request.")

    try:
        # Request থেকে JSON parse
        req_body = req.get_json()
        subject = req_body.get("subject", "Test Email from Azure Function")
        content = req_body.get("content", "This is a test email body.")

        # Sender/Receiver fix করে দেওয়া (আপনার দেওয়া data অনুযায়ী)
        sender = "DoNotReply@ed606959-b263-4a31-b27e-090fcddddb2d.azurecomm.net"
        to_email = "faruk.cse.pust12@gmail.com"

        # Azure Communication Service connection string
        conn_str = "endpoint=https://my-email-service.asiapacific.communication.azure.com/;accesskey=2UnN2o8oy7QBfS2bnXzGRcqSNVOUDEOtqVCnUxNREve3oIrLCTITJQQJ99BHACULyCpSubbrAAAAAZCSMEoC"

        client = EmailClient.from_connection_string(conn_str)

        message = {
            "senderAddress": sender,
            "recipients": {
                "to": [{"address": to_email}]
            },
            "content": {
                "subject": subject,
                "plainText": content
            }
        }

        poller = client.begin_send(message)
        result = poller.result()

        logging.info(f"Email sent successfully! MessageId = {result['messageId']}")
        return func.HttpResponse(
            f"Mail sent successfully to {to_email}!",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return func.HttpResponse(
            f"Failed to send mail. Error: {str(e)}",
            status_code=500
        )
