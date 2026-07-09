import cloudinary
import cloudinary.uploader



CLOUDINARY_URL = "https://console.cloudinary.com/app/c-8e00a7b43d01251677e2cf011c1f23/settings/api-keys"

API_KEY = "355952577269636"
API_SECRET = "Mn5KxPwfi7QXVjjdSSItXaq6WjE"

cloudinary.config(
cloud_name = "dq9uhfa4r",
api_key = API_KEY,
api_secret = API_SECRET
)

def upload_pdf(pdf_file):
    res = cloudinary.uploader.upload(f"receipts/{pdf_file}.pdf")
    print(res)
    return res.get("secure_url") 

upload_pdf("generated")


    