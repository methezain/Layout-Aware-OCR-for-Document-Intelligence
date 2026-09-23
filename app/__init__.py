import os

# Paddle 3.x oneDNN/PIR crashes on CPU unless this is set before Paddle imports.
os.environ["FLAGS_use_mkldnn"] = "0"
