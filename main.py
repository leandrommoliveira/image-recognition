from PIL import Image
import pytesseract
import os

if os.path.exists("output.txt"):
    os.remove("output.txt")

# Simple image to string
output = pytesseract.image_to_string(Image.open('image.png'))
print(output)

f = open("output.txt", "w+")
f.write(output)
f.close()

