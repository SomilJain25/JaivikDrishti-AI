import io
from PIL import Image
import requests

img = Image.new('RGB', (224, 224), (128, 200, 100))
buf = io.BytesIO()
img.save(buf, format='PNG')
buf.seek(0)

r = requests.post('http://127.0.0.1:8000/predict', files={'file': ('test.png', buf.getvalue(), 'image/png')})
print('status', r.status_code)
print(r.text)
