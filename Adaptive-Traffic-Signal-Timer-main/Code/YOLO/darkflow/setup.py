import os
import importlib.util
import sys
from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
import numpy as np

# Fallback NMS implementation with Numba optimization
from numba import jit

@jit(nopython=True)
def calculate_iou(box1_x, box1_y, box1_w, box1_h, 
                  box2_x, box2_y, box2_w, box2_h):
    """
    Calculate Intersection over Union between two boxes using Numba
    
    Args:
        box1_x, box1_y, box1_w, box1_h: Coordinates and dimensions of first box
        box2_x, box2_y, box2_w, box2_h: Coordinates and dimensions of second box
    
    Returns:
        Intersection over Union score
    """
    x1 = max(box1_x, box2_x)
    y1 = max(box1_y, box2_y)
    x2 = min(box1_x + box1_w, box2_x + box2_w)
    y2 = min(box1_y + box1_h, box2_y + box2_h)

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    union = (box1_w * box1_h + box2_w * box2_h - intersection)
    
    return intersection / union if union > 0 else 0.0

@jit(nopython=True)
def non_max_suppression(boxes, iou_threshold=0.5):
    """
    Numba-optimized Non-Maximum Suppression implementation
    
    Args:
        boxes: 2D numpy array of detection boxes
               Each row: [x, y, width, height, confidence]
        iou_threshold: Intersection over Union threshold
    
    Returns:
        Filtered boxes after non-maximum suppression
    """
    # Sort boxes by confidence in descending order
    sorted_indices = np.argsort(boxes[:, 4])[::-1]
    sorted_boxes = boxes[sorted_indices]
    
    keep = []
    while len(sorted_boxes) > 0:
        best_box = sorted_boxes[0]
        keep.append(best_box)
        
        # Filter out boxes with high IoU
        filtered_indices = []
        for i in range(1, len(sorted_boxes)):
            iou = calculate_iou(
                best_box[0], best_box[1], best_box[2], best_box[3],
                sorted_boxes[i][0], sorted_boxes[i][1], 
                sorted_boxes[i][2], sorted_boxes[i][3]
            )
            if iou <= iou_threshold:
                filtered_indices.append(i)
        
        sorted_boxes = sorted_boxes[filtered_indices]
    
    return np.array(keep)

# Version loading function
def load_version():
    version_path = os.path.join('.', 'darkflow', 'version.py')
    try:
        spec = importlib.util.spec_from_file_location("version", version_path)
        version_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(version_module)
        return version_module.__version__
    except Exception as e:
        print(f"Could not load version: {e}")
        return "0.0.0"

# Get VERSION
VERSION = load_version()

# Setup configuration
setup(
    version=VERSION,
    name='darkflow',
    description='Darkflow with Numba Optimization',
    license='GPLv3',
    url='https://github.com/thtrieu/darkflow',
    packages=find_packages(),
    scripts=['flow'],
    install_requires=[
        'numpy',
        'numba',  # Replace Cython with Numba
    ]
)