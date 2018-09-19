# footer taking a pillow `image`, and print it in png/base64
import io
import base64
with io.BytesIO() as output:
    image.save(output, format='png')
    print(base64.b64encode(output.getvalue()).decode())
