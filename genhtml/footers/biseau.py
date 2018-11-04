# Use asp code in `asp`, or config in `config` as parameter for biseau.
#  render the image, or gif if `isgif` is thruthy.
import os
import io
import base64
import biseau
import tempfile

asp = globals().get('asp', None)
isgif = globals().get('isgif', None)
config = globals().get('config', None)
duration = globals().get('duration', 1000)

def build(fnames:list) -> bytes:
    if isgif:
        return biseau.gif_from_filenames([tmpfile], duration=duration)
    else:
        with io.BytesIO() as output:
            biseau.single_image_from_filenames([tmpfile], return_image=True).save(output, 'png')
            return output.getvalue()

if asp:
    with tempfile.NamedTemporaryFile('w', suffix='.lp', delete=False) as fd:
        tmpfile = fd.name
        fd.write(asp)
    databytes = build([tmpfile])
    os.unlink(tmpfile)
elif config:
    pipeline = biseau.core.build_pipeline.from_json(config)
    databytes = build(pipeline)

print(base64.b64encode(databytes).decode())
