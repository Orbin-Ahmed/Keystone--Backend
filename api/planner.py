from ultralytics import YOLO
import json
from PIL import Image
import math
import os
import pytesseract
import cv2
import numpy as np
from uuid import uuid4
from io import BytesIO
import base64
import requests
from roboflow import Roboflow

def detect_walls_and_shapes_in_image(image_file):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        uploaded_image = Image.open(image_file)
        # wall_model_path = os.path.join(current_dir, 'checkpoints', 'best_27k_50.pt')
        # wall_res = wall_model.predict(uploaded_image, conf=0.1)
        # wall_model = YOLO(wall_model_path)
        # wall_filtered_boxes = [
        #     box for box in wall_res[0].boxes
        #     if wall_model.names[int(box.cls.item())] == 'wall'
        # ]
        
        shape_model_path = os.path.join(current_dir, 'checkpoints', 'best_1600_box_100.pt')
        
        buffered = BytesIO()
        uploaded_image.save(buffered, format="JPEG")
        encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        url = "https://detect.roboflow.com/wall-detection-by-orbin/4?api_key=xiUZdGv8HlJRS3BxzY4O&overlap=0.50&confidence=0.2"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = f"image={encoded_image}"
        
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception(
                f"Wall detection API returned status code {response.status_code}"
            )
            
        wall_data = response.json()
        predictions = wall_data.get("predictions", [])
        
        wall_filtered_boxes = []
        for pred in predictions:
            if pred.get("class") == "wall" and pred.get("confidence", 0) > 0.2:
                x = pred["x"]
                y = pred["y"]
                w = pred["width"]
                h = pred["height"]
                x1 = x - (w / 2)
                y1 = y - (h / 2)
                x2 = x + (w / 2)
                y2 = y + (h / 2)
                synthetic_box = {
                    "xyxy": [[x1, y1, x2, y2]]
                }
                wall_filtered_boxes.append(synthetic_box)
        
        wall_lines_json = extract_wall_lines(wall_filtered_boxes)
        shape_model = YOLO(shape_model_path)
        shape_res = shape_model.predict(uploaded_image, conf=0.25)
        
        available_classes = [
            "DOOR", "DOUBLE DOOR", "FOLDING DOOR", "SLIDING DOOR", "WINDOW"
        ]
        shape_filtered_boxes = [
            box for box in shape_res[0].boxes
            if shape_model.names[int(box.cls.item())].upper() in available_classes
        ]
        
        shapes_json = extract_shapes(
            shape_filtered_boxes, wall_lines_json["lines"], shape_model
        )
        
        room_names_json = detect_room_names(uploaded_image)
        
        result = {
            "lines": wall_lines_json["lines"],
            "shapes": shapes_json["shapes"],
            "roomNames": room_names_json,
        }
        
        return json.dumps(result, indent=4)
    
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=4)

def extract_wall_lines(filtered_boxes):
    wall_lines = []

    for box in filtered_boxes:
        x_min, y_min, x_max, y_max = box.xyxy[0].tolist()
        width = abs(x_max - x_min)
        height = abs(y_max - y_min)
        thickness = min(width, height) if min(width, height) > 0 else 8
        id = str(uuid4())

        if width > height:
            y_middle = (y_max + y_min) / 2
            wall_lines.append({
                "id": id,
                "points": [x_min, y_middle, x_max, y_middle],
                "thickness": thickness if thickness < 0 else 8
            })
        else:
            x_middle = (x_max + x_min) / 2
            wall_lines.append({
                "id": id,
                "points": [x_middle, y_max, x_middle, y_min],
                "thickness": thickness if thickness < 0 else 8
            })
        
    processed_walls = process_walls(wall_lines, alignment_threshold=10, gap_threshold=20, corner_threshold=20)
       
    return {"lines": processed_walls}

def extract_shapes(filtered_boxes, wall_lines, shape_model):
    shapes = []

    for box in filtered_boxes:
        x_min, y_min, x_max, y_max = box.xyxy[0].tolist()
        class_idx = int(box.cls.item())
        class_name = shape_model.names[class_idx].upper()

        if class_name == 'WINDOW':
            shape_type = 'window'
            width = 70
            height = 8
            image = 'window'
        elif class_name in ['DOOR', 'DOUBLE DOOR', 'FOLDING DOOR', 'SLIDING DOOR']:
            shape_type = 'door'
            width = 40
            height = 60
            image = 'door'
        else:
            continue

        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        wall_id = find_closest_wall_id(x_center, y_center, wall_lines)
        
        shape = align_shape_to_wall({
            "id": str(uuid4()),
            "type": shape_type,
            "x": x_center,
            "y": y_center,
            "width": width,
            "height": height,
            "image": image,
            "wallId": wall_id
        }, wall_lines, wall_id)

        shapes.append(shape)

    return {"shapes": shapes}

def align_shape_to_wall(shape, wall_lines, wall_id):
    wall = next((wall for wall in wall_lines if wall["id"] == wall_id), None)
    if wall is None:
        return shape

    x1, y1, x2, y2 = wall["points"]
    angle_radians = calculate_wall_angle(x1, y1, x2, y2)
    angle_degrees = math.degrees(angle_radians)

    # shape["rotation"] = angle_degrees
    shape["rotation"] = (angle_degrees + 180) % 360
    x_center, y_center = shape["x"], shape["y"]
    dx = x2 - x1
    dy = y2 - y1
    denominator = dx ** 2 + dy ** 2
    if denominator == 0:
        t = 0
    else:
        t = ((x_center - x1) * dx + (y_center - y1) * dy) / denominator
    t = max(0, min(1, t))
    x_closest = x1 + t * dx
    y_closest = y1 + t * dy

    wall_length = math.hypot(dx, dy)
    if wall_length == 0:
        normal_dx, normal_dy = 0, 0
    else:
        wall_unit_dx = dx / wall_length
        wall_unit_dy = dy / wall_length
        normal_dx = -wall_unit_dy
        normal_dy = wall_unit_dx

    offset_distance = 4
    shape["x"] = x_closest + normal_dx * offset_distance
    shape["y"] = y_closest + normal_dy * offset_distance

    return shape

def find_closest_wall_id(x, y, wall_lines):
    min_distance = None
    closest_wall_id = None

    for wall in wall_lines:
        x1, y1, x2, y2 = wall["points"]
        distance = point_to_line_distance(x, y, x1, y1, x2, y2)
        if min_distance is None or distance < min_distance:
            min_distance = distance
            closest_wall_id = wall["id"]

    return closest_wall_id

def point_to_line_distance(x0, y0, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return ((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5

    t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx ** 2 + dy ** 2)
    t = max(0, min(1, t))
    x_closest = x1 + t * dx
    y_closest = y1 + t * dy
    distance = ((x0 - x_closest) ** 2 + (y0 - y_closest) ** 2) ** 0.5
    return distance

def calculate_wall_angle(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1)


# Process Wall Function 
def wall_orientation(wall, angle_threshold=15):
    x1, y1, x2, y2 = wall['points']
    dx = x2 - x1
    dy = y2 - y1
    angle = math.degrees(math.atan2(dy, dx))
    angle = (angle + 360) % 180
    if angle < angle_threshold or angle > (180 - angle_threshold):
        return 'horizontal'
    elif abs(angle - 90) < angle_threshold:
        return 'vertical'
    else:
        return 'other'

def walls_are_aligned_and_close(wall1, wall2, alignment_threshold, gap_threshold):
    orientation1 = wall_orientation(wall1)
    orientation2 = wall_orientation(wall2)

    if orientation1 != orientation2:
        return False

    if orientation1 == 'horizontal':
        y1 = (wall1['points'][1] + wall1['points'][3]) / 2
        y2 = (wall2['points'][1] + wall2['points'][3]) / 2
        if abs(y1 - y2) > alignment_threshold:
            return False

        x1_start = min(wall1['points'][0], wall1['points'][2])
        x1_end = max(wall1['points'][0], wall1['points'][2])
        x2_start = min(wall2['points'][0], wall2['points'][2])
        x2_end = max(wall2['points'][0], wall2['points'][2])

        if x1_end + gap_threshold >= x2_start - gap_threshold and x2_end + gap_threshold >= x1_start - gap_threshold:
            return True
        else:
            return False

    elif orientation1 == 'vertical':
        x1 = (wall1['points'][0] + wall1['points'][2]) / 2
        x2 = (wall2['points'][0] + wall2['points'][2]) / 2
        if abs(x1 - x2) > alignment_threshold:
            return False

        y1_start = min(wall1['points'][1], wall1['points'][3])
        y1_end = max(wall1['points'][1], wall1['points'][3])
        y2_start = min(wall2['points'][1], wall2['points'][3])
        y2_end = max(wall2['points'][1], wall2['points'][3])

        if y1_end + gap_threshold >= y2_start - gap_threshold and y2_end + gap_threshold >= y1_start - gap_threshold:
            return True
        else:
            return False

    else:
        return False

def merge_walls(wall1, wall2):
    orientation = wall_orientation(wall1)
    new_id = str(uuid4())

    if orientation == 'horizontal':
        y_coords = [wall1['points'][1], wall1['points'][3], wall2['points'][1], wall2['points'][3]]
        y_avg = sum(y_coords) / len(y_coords)
        x_coords = [wall1['points'][0], wall1['points'][2], wall2['points'][0], wall2['points'][2]]
        x_start = min(x_coords)
        x_end = max(x_coords)
        new_wall = {
            'id': new_id,
            'points': [x_start, y_avg, x_end, y_avg],
            'thickness': (wall1['thickness'] + wall2['thickness']) / 2
        }
        return new_wall

    elif orientation == 'vertical':
        x_coords = [wall1['points'][0], wall1['points'][2], wall2['points'][0], wall2['points'][2]]
        x_avg = sum(x_coords) / len(x_coords)
        y_coords = [wall1['points'][1], wall1['points'][3], wall2['points'][1], wall2['points'][3]]
        y_start = min(y_coords)
        y_end = max(y_coords)
        new_wall = {
            'id': new_id,
            'points': [x_avg, y_start, x_avg, y_end],
            'thickness': (wall1['thickness'] + wall2['thickness']) / 2
        }
        return new_wall

    else:
        return wall1

def merge_aligned_walls(wall_lines, alignment_threshold, gap_threshold):
    walls_to_process = wall_lines.copy()
    merged_walls = []

    while walls_to_process:
        current_wall = walls_to_process.pop(0)
        i = 0
        while i < len(walls_to_process):
            other_wall = walls_to_process[i]
            if walls_are_aligned_and_close(current_wall, other_wall, alignment_threshold, gap_threshold):
                current_wall = merge_walls(current_wall, other_wall)
                walls_to_process.pop(i)
                i = 0
            else:
                i += 1
        merged_walls.append(current_wall)

    return merged_walls

def connect_corner_walls(wall_lines, corner_threshold):
    walls = wall_lines.copy()

    for i in range(len(walls)):
        wall1 = walls[i]
        orientation1 = wall_orientation(wall1)

        for j in range(i + 1, len(walls)):
            wall2 = walls[j]
            orientation2 = wall_orientation(wall2)

            if (orientation1 == 'vertical' and orientation2 == 'horizontal') or \
               (orientation1 == 'horizontal' and orientation2 == 'vertical'):

                endpoints_wall1 = [
                    (wall1['points'][0], wall1['points'][1]),
                    (wall1['points'][2], wall1['points'][3])
                ]
                endpoints_wall2 = [
                    (wall2['points'][0], wall2['points'][1]),
                    (wall2['points'][2], wall2['points'][3])
                ]

                for idx1, (x1, y1) in enumerate(endpoints_wall1):
                    for idx2, (x2, y2) in enumerate(endpoints_wall2):
                        if abs(x1 - x2) <= corner_threshold and abs(y1 - y2) <= corner_threshold:
                            if orientation1 == 'vertical' and orientation2 == 'horizontal':
                                if idx1 == 0:
                                    walls[i]['points'][1] = y2
                                else:
                                    walls[i]['points'][3] = y2
                                if idx2 == 0:
                                    walls[j]['points'][0] = x1
                                else:
                                    walls[j]['points'][2] = x1
                            elif orientation1 == 'horizontal' and orientation2 == 'vertical':
                                if idx1 == 0:
                                    walls[i]['points'][0] = x2
                                else:
                                    walls[i]['points'][2] = x2
                                if idx2 == 0:
                                    walls[j]['points'][1] = y1
                                else:
                                    walls[j]['points'][3] = y1
    return walls

def trim_walls_at_intersections(walls, max_trim_amount=15):
    walls = walls.copy()
    for i in range(len(walls)):
        wall = walls[i]
        orientation = wall_orientation(wall)
        x1, y1, x2, y2 = wall['points']

        if orientation == 'horizontal':
            x_start = min(x1, x2)
            x_end = max(x1, x2)
            y_fixed = y1

            for j in range(len(walls)):
                if i == j:
                    continue
                other_wall = walls[j]
                other_orientation = wall_orientation(other_wall)

                if other_orientation == 'vertical':
                    xv, yv1, xv2, yv2 = other_wall['points']
                    yv_start = min(yv1, yv2)
                    yv_end = max(yv1, yv2)
                    xv_fixed = xv

                    if yv_start <= y_fixed <= yv_end and x_start < xv_fixed < x_end:
                        if x1 < x2:
                            trim_amount = x2 - xv_fixed
                            if 0 < trim_amount <= max_trim_amount:
                                x2 = xv_fixed
                                wall['points'] = [x1, y1, x2, y2]
                        else:
                            trim_amount = xv_fixed - x2
                            if 0 < trim_amount <= max_trim_amount:
                                x2 = xv_fixed
                                wall['points'] = [x1, y1, x2, y2]

        elif orientation == 'vertical':
            y_start = min(y1, y2)
            y_end = max(y1, y2)
            x_fixed = x1

            for j in range(len(walls)):
                if i == j:
                    continue
                other_wall = walls[j]
                other_orientation = wall_orientation(other_wall)

                if other_orientation == 'horizontal':
                    xh1, yh, xh2, yh2 = other_wall['points']
                    xh_start = min(xh1, xh2)
                    xh_end = max(xh1, xh2)
                    yh_fixed = yh

                    if xh_start <= x_fixed <= xh_end and y_start < yh_fixed < y_end:
                        if y1 < y2:
                            trim_amount = y2 - yh_fixed
                            if 0 < trim_amount <= max_trim_amount:
                                y2 = yh_fixed
                                wall['points'] = [x1, y1, x2, y2]
                        else:
                            trim_amount = yh_fixed - y2
                            if 0 < trim_amount <= max_trim_amount:
                                y2 = yh_fixed
                                wall['points'] = [x1, y1, x2, y2]
    return walls

def process_walls(wall_lines, alignment_threshold=20, gap_threshold=30, corner_threshold=30):
    walls = merge_aligned_walls(wall_lines, alignment_threshold, gap_threshold)
    walls = connect_corner_walls(walls, corner_threshold)
    walls = trim_walls_at_intersections(walls)
    return walls

# Rooms function 
def detect_room_names(image):
    open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
    common_room_names = {
        "KITCHEN", "BEDROOM", "DINING", "BATHROOM", "LIVING", "KID'S ROOM",
        "MASTER BEDROOM", "GUEST ROOM", "STUDY", "HALL", "OFFICE", "GARAGE",
        "STORE", "PANTRY", "LAUNDRY", "BALCONY", "TOILET", "MAJLIS", "LOBBY",
        "ENTRANCE", "WOMEN'S DINING", "WOMEN'S MAJLIS", "MEN'S MAJLIS", 
        "LIVING ROOM", "BATH", "TERRACE", "ENTRANCE", "GUEST BEDROOM", 
        "FORMAL SEATING", "FAMILY LIVING", "INFORMAL LIVING", "FAMILY DINING", 
        "GUEST TOILET", "FORMAL DINING", "BATH", "WASH"
    }

    rooms = []
    i = 0
    while i < len(data['text']):
        text = data['text'][i].strip()
        if not text:
            i += 1
            continue

        text_upper = text.upper()
        if text_upper in common_room_names:
            x = data['left'][i]
            y = data['top'][i]
            width = data['width'][i]
            height = data['height'][i]
            x_center = x + width / 2
            y_center = y + height / 2
            rooms.append({
                "x": x_center,
                "y": y_center,
                "name": text_upper
            })
            i += 1
            continue
        
        combined_text = text_upper
        x_min = data['left'][i]
        y_min = data['top'][i]
        width_total = data['width'][i]
        
        j = i + 1
        while j < len(data['text']) and data['text'][j].strip():
            next_text = data['text'][j].strip().upper()
            combined_text += " " + next_text
            
            if combined_text in common_room_names:
                x_max = data['left'][j] + data['width'][j]
                width_total = x_max - x_min
                height_total = max(data['height'][i:j+1])
                x_center = x_min + width_total / 2
                y_center = y_min + height_total / 2
                rooms.append({
                    "x": x_center,
                    "y": y_center,
                    "name": combined_text
                })
                i = j
                break
            
            j += 1
        i += 1
    return rooms
