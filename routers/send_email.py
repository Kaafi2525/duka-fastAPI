# ===============================
# IMPORTS
# ===============================
import mailtrap as mt
from config import settings


# ===============================
# MAILTRAP CONFIG
# ===============================
MAILTRAP_TOKEN = settings.mailtrap_token


# ===============================
# SEND EMAIL FUNCTION
# ===============================
def send_email(to_email, subject, message):

    try:
        if not MAILTRAP_TOKEN:
            return {
                "success": False,
                "error": "MAILTRAP_TOKEN is not configured",
            }

        mail = mt.Mail(

            sender=mt.Address(
                email=settings.mailtrap_sender_email,
                name=settings.mailtrap_sender_name
            ),

            to=[
                mt.Address(email=to_email)
            ],

            subject=subject,

            text=message
        )

        client = mt.MailtrapClient(
            token=MAILTRAP_TOKEN
        )

        response = client.send(mail)

        return response

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ===============================
# TEST
# ===============================
if __name__ == "__main__":

    response = send_email(
        "mdan10532@gmail.com",
        "Payment Successful",
        "Hello, your payment was successful. Thank you for using our service!"
    )

    print(response)
