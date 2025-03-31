# model_config.py


import torch
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# This will be filled in by the notebook
model = None
