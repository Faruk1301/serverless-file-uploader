import logging
import azure.functions as func
from azure.communication.email import EmailClient

def main(myblob: func.InputStream):
    logging.info(f"File uploaded: {myblob.name}, Size: {myblob.length} bytes")

    client = EmailClient.from_connection_string("YOUR_ACS_CONNECTION_STRING")

    message = {
        "senderAddress": "Donotreply@ed606959-b263-4a31-b27e-090fcddddb2d.azurecomm.net",
        "recipients": {"to": [{"address": "faruk.cse.pust12@gmail.com"}]},
        "content": {
            "subject": "Blob Upload Notification",
            "plainText": f"A new file '{myblob.name}' was uploaded!"
        }
    }
    poller = client.begin_send(message)
    poller.result()
