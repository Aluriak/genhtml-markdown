import base64
import plotly.io as pio

# get arguments, if they exists
kwargs = {}
if globals().get('width'):
    kwargs['width'] = width
if globals().get('height'):
    kwargs['height'] = height
if globals().get('scale'):
    kwargs['scale'] = scale
if globals().get('figure'):
    plot = figure

img_bytes = pio.to_image(
    plot,
    format='png',
    **kwargs
)

print(base64.b64encode(img_bytes.getvalue()).decode())
