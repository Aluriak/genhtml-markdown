# Use pyplot and dot to render `graph` in png
# Assume graph is a networkx Graph.

# get the dot
import io
import base64
from networkx.drawing.nx_pydot import write_dot
with io.StringIO() as output:
    write_dot(graph, output)
    dot = output.getvalue()

# get the png in base64
import subprocess
proc = subprocess.Popen(['dot', '-Tpng'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
stdout, _ = proc.communicate(dot.encode())
import base64
print(base64.b64encode(stdout).decode())
