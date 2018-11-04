# footer taking pillow Image instances in `frames`, and print it in gif/base64
# if `duration` exists, it will be used as a number of millisecond for each frame.
# same for `loop`.
import io
import base64

first, *lasts = frames
duration = int(globals().get('duration', 1000))
loop = int(globals().get('loop', 0))

with io.BytesIO() as output:
    first.save(output, append_images=lasts, duration=duration, loop=loop, save_all=True)
    print(base64.b64encode(output.getvalue()).decode())
