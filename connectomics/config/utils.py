import os
import warnings
import argparse
from yacs.config import CfgNode

def update_inference_cfg(cfg: CfgNode):
    r"""Overwrite configurations (cfg) when running mode is inference. Please 
    note that None type is only supported in YACS>=0.1.8.
    """
    # Dataset configurations:
    if cfg.INFERENCE.INPUT_PATH is not None:
        cfg.DATASET.INPUT_PATH = cfg.INFERENCE.INPUT_PATH
    cfg.DATASET.IMAGE_NAME = cfg.INFERENCE.IMAGE_NAME
    cfg.DATASET.OUTPUT_PATH = cfg.INFERENCE.OUTPUT_PATH
    if cfg.INFERENCE.PAD_SIZE is not None:
        cfg.DATASET.PAD_SIZE = cfg.INFERENCE.PAD_SIZE

    # Model configurations:
    if cfg.INFERENCE.INPUT_SIZE is not None:
        cfg.MODEL.INPUT_SIZE = cfg.INFERENCE.INPUT_SIZE
    if cfg.INFERENCE.OUTPUT_SIZE is not None:
        cfg.MODEL.OUTPUT_SIZE = cfg.INFERENCE.OUTPUT_SIZE

    for topt in cfg.MODEL.TARGET_OPT:
        # For multi-class semantic segmentation and quantized distance
        # transform, no activation function is applied at the output layer 
        # during training. For inference where the output is assumed to be 
        # in (0,1), we apply softmax. 
        if topt[0] in ['5', '9'] and cfg.MODEL.OUTPUT_ACT == 'none':
            cfg.MODEL.OUTPUT_ACT = 'softmax'
            break

def save_all_cfg(cfg: CfgNode, output_dir: str):
    r"""Save configs in the output directory.
    """
    # Save config.yaml in the experiment directory after combine all 
    # non-default configurations from yaml file and command line.
    path = os.path.join(output_dir, "config.yaml")
    with open(path, "w") as f:
        f.write(cfg.dump())
    print("Full config saved to {}".format(path))

def overwrite_cfg(cfg: CfgNode, args: argparse.Namespace):
    r"""Overwrite some configs given configs or args with higher priority.
    """
    # Distributed training:
    if args.distributed:
        cfg.SYSTEM.DISTRIBUTED = True
        cfg.SYSTEM.PARALLEL = 'DDP'

    # Target options:
    for topt in cfg.MODEL.TARGET_OPT:
        if topt[0] == '5': # quantized distance transform
            cfg.MODEL.OUT_PLANES = 11
            assert len(cfg.MODEL.TARGET_OPT) == 1, \
                "Multi-task learning with quantized distance transform " \
                "is currently not supported."

    # Model I/O size
    for x in cfg.MODEL.INPUT_SIZE:
        if x % 2 == 0 and not cfg.MODEL.POOING_LAYER:
            warnings.warn(
                "When downsampling by stride instead of using pooling " \
                "layers, the cfg.MODEL.INPUT_SIZE are expected to contain " \
                "numbers of 2n+1 to avoid feature mis-matching, " \
                "but get {}".format(cfg.MODEL.INPUT_SIZE))
            break
        if x % 2 == 1 and cfg.MODEL.POOING_LAYER:
            warnings.warn(
                "When downsampling by pooling layers the cfg.MODEL.INPUT_SIZE " \
                "are expected to contain even numbers to avoid feature mis-matching, " \
                "but get {}".format(cfg.MODEL.INPUT_SIZE))
            break
        