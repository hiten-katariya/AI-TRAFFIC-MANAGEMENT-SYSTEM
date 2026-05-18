import os
from PIL import Image, ImageDraw, ImageFont
import logging
from datetime import datetime
import argparse
from ultralytics import YOLO

class VehicleDetector:
    def __init__(self, model_version='yolov8s', confidence_threshold=0.3, custom_weights=None):
        self.setup_logging()
        try:
            if custom_weights and os.path.exists(custom_weights):
                self.logger.info(f"Loading custom weights from: {custom_weights}")
                self.model = YOLO(custom_weights)
            else:
                model_path = f"{model_version}.pt"
                self.logger.info(f"Loading pre-trained YOLOv8 model: {model_version}")
                self.model = YOLO(model_path)
            self.conf_threshold = confidence_threshold
            self.vehicle_classes = [
                'bicycle', 'motorcycle', 'car', 'bus', 'truck',
                'train'
            ]
            self.logger.info(f"Vehicle detector initialized successfully with {model_version}")
        except Exception as e:
            self.logger.error(f"Failed to initialize detector: {e}")
            raise

    def setup_logging(self):
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.join(log_dir, f'vehicle_detection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def detect_vehicles(self, input_path, output_path, filename, draw_boxes=True, save_crops=False):
        try:
            img_path = os.path.join(input_path, filename)
            class_counts = {vehicle_class: 0 for vehicle_class in self.vehicle_classes}
            results = self.model(img_path, conf=self.conf_threshold)
            if draw_boxes:
                img = Image.open(img_path)
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except IOError:
                    font = ImageFont.load_default()
            vehicle_count = 0
            crops_dir = None
            if save_crops:
                crops_dir = os.path.join(output_path, "crops", os.path.splitext(filename)[0])
                os.makedirs(crops_dir, exist_ok=True)
            detections = results[0]
            for i, detection in enumerate(detections.boxes.data):
                *xyxy, conf, cls_id = detection.tolist()
                xyxy = [int(x) for x in xyxy]
                label = detections.names[int(cls_id)]
                if label in self.vehicle_classes:
                    if draw_boxes:
                        draw.rectangle(xyxy, outline=(0, 255, 0), width=3)
                        label_text = f"{label} {conf:.2f}"
                        draw.text((xyxy[0], xyxy[1]-20), label_text, fill=(0,0,0), font=font)
                    class_counts[label] += 1
                    vehicle_count += 1
                    if save_crops:
                        crop = img.crop(xyxy)
                        crop_path = os.path.join(crops_dir, f"{label}_{i}_{conf:.2f}.jpg")
                        crop.save(crop_path)
            if draw_boxes:
                output_filename = os.path.join(output_path, f"output_{filename}")
                img.save(output_filename)
                self.logger.info(f'Output image stored at: {output_filename}')
            self.logger.info(f'Processed {filename}: {vehicle_count} vehicles detected')
            for vehicle_class, count in class_counts.items():
                if count > 0:
                    self.logger.info(f'  - {vehicle_class}: {count}')
            return {
                "total_count": vehicle_count,
                "class_counts": {k: v for k, v in class_counts.items() if v > 0},
                "filename": filename
            }
        except Exception as e:
            self.logger.error(f"Error processing {filename}: {e}")
            return {"total_count": 0, "class_counts": {}, "filename": filename}

def main():
    parser = argparse.ArgumentParser(description='YOLOv8 Vehicle Detection')
    parser.add_argument('--input', default='test_images', help='Input directory for images')
    parser.add_argument('--output', default='output_images', help='Output directory for processed images')
    parser.add_argument('--model', default='yolov8s', help='YOLOv8 model version (yolov8n, yolov8s, yolov8m, yolov8l, yolov8x)')
    parser.add_argument('--confidence', type=float, default=0.3, help='Confidence threshold')
    parser.add_argument('--weights', help='Path to custom weights file')
    parser.add_argument('--no-boxes', action='store_true', help='Do not draw bounding boxes')
    parser.add_argument('--save-crops', action='store_true', help='Save cropped detections')
    args = parser.parse_args()
    try:
        detector = VehicleDetector(
            model_version=args.model,
            confidence_threshold=args.confidence,
            custom_weights=args.weights
        )
        input_path = os.path.join(os.getcwd(), args.input)
        output_path = os.path.join(os.getcwd(), args.output)
        os.makedirs(input_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)
        image_files = [f for f in os.listdir(input_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not image_files:
            detector.logger.warning("No image files found in the input directory")
            return
        detection_results = []
        for filename in image_files:
            results = detector.detect_vehicles(
                input_path, 
                output_path, 
                filename,
                draw_boxes=not args.no_boxes,
                save_crops=args.save_crops
            )
            detection_results.append(results)
        total_vehicles = sum(result["total_count"] for result in detection_results)
        if total_vehicles > 0:
            total_by_class = {}
            for result in detection_results:
                for cls, count in result["class_counts"].items():
                    total_by_class[cls] = total_by_class.get(cls, 0) + count
            detector.logger.info(f"Processed {len(image_files)} images")
            detector.logger.info(f"Total vehicles detected: {total_vehicles}")
            detector.logger.info("Vehicle distribution:")
            for cls, count in total_by_class.items():
                detector.logger.info(f"  - {cls}: {count} ({count/total_vehicles*100:.1f}%)")
        else:
            detector.logger.info(f"Processed {len(image_files)} images")
            detector.logger.info("No vehicles detected")
    except Exception as e:
        logging.error(f"Unexpected error in main execution: {e}")

if __name__ == "__main__":
    main()