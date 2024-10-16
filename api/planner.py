from ultralytics import YOLO
import json
from PIL import Image
import math
from .helper import ensure_model_exists

def detect_walls_and_shapes_in_image(image_file):
    try:
        # wall_model_path = '../best_wall_7k_100.pt'
        # shape_model_path = '../best_1600_box_100.pt'
        wall_model_path = 'checkpoints/best_wall_7k_100.pt'
        shape_model_path = 'checkpoints/best_1600_box_100.pt'
        wall_model = YOLO(wall_model_path)
        uploaded_image = Image.open(image_file)
        wall_res = wall_model.predict(uploaded_image, conf=0.1)
        
        wall_filtered_boxes = [
            box for box in wall_res[0].boxes
            if wall_model.names[int(box.cls.item())] == 'wall'
        ]
        
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
        
        result = {
            "lines": wall_lines_json["lines"],
            "shapes": shapes_json["shapes"]
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

        if width > height:
            y_middle = (y_max + y_min) / 2
            wall_lines.append({
                "points": [x_min, y_middle, x_max, y_middle],
                "thickness": thickness if thickness < 0 else 8
            })
        else:
            x_middle = (x_max + x_min) / 2
            wall_lines.append({
                "points": [x_middle, y_max, x_middle, y_min],
                "thickness": thickness if thickness < 0 else 8
            })
            
    wall_lines = extend_close_walls(wall_lines, threshold=30)
    wall_lines = merge_overlapping_walls(wall_lines, alignment_threshold=30)
    wall_lines = remove_redundant_walls(wall_lines, proximity_threshold=10)
       
    return {"lines": wall_lines}

def merge_overlapping_walls(wall_lines, alignment_threshold):
    merged_walls = []
    while wall_lines:
        current_wall = wall_lines.pop(0)
        x_start, y_start, x_end, y_end = current_wall["points"]
        thickness = current_wall["thickness"]
        is_horizontal = abs(x_end - x_start) > abs(y_end - y_start)
        merged = True

        while merged:
            merged = False
            new_wall_lines = []
            for wall in wall_lines:
                x2_start, y2_start, x2_end, y2_end = wall["points"]
                is_horizontal_j = abs(x2_end - x2_start) > abs(y2_end - y2_start)

                if is_horizontal == is_horizontal_j:
                    if is_horizontal:
                        if abs(y_start - y2_start) <= alignment_threshold:
                            if max(x_start, x2_start) <= min(x_end, x2_end):
                                x_start = min(x_start, x2_start)
                                x_end = max(x_end, x2_end)
                                y_start = (y_start + y2_start) / 2
                                y_end = y_start
                                merged = True
                                continue
                    else:
                        if abs(x_start - x2_start) <= alignment_threshold:
                            if max(y_start, y2_start) <= min(y_end, y2_end):
                                y_start = min(y_start, y2_start)
                                y_end = max(y_end, y2_end)
                                x_start = (x_start + x2_start) / 2
                                x_end = x_start
                                merged = True
                                continue
                new_wall_lines.append(wall)

            wall_lines = new_wall_lines

        merged_walls.append({
            "points": [x_start, y_start, x_end, y_end],
            "thickness": thickness
        })

    return merged_walls

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
        wall_index = find_closest_wall_index(x_center, y_center, wall_lines)
        
        shape = align_shape_to_wall({
            "type": shape_type,
            "x": x_center,
            "y": y_center,
            "width": width,
            "height": height,
            "image": image
        }, wall_lines, wall_index)

        shapes.append(shape)

    return {"shapes": shapes}

def align_shape_to_wall(shape, wall_lines, wall_index):
    wall = wall_lines[wall_index]
    x1, y1, x2, y2 = wall["points"]
    angle_radians = calculate_wall_angle(x1, y1, x2, y2)
    angle_degrees = math.degrees(angle_radians)

    shape["rotation"] = angle_degrees
    x_center, y_center = shape["x"], shape["y"]
    t = ((x_center - x1) * (x2 - x1) + (y_center - y1) * (y2 - y1)) / ((x2 - x1) ** 2 + (y2 - y1) ** 2)
    t = max(0, min(1, t))
    x_closest = x1 + t * (x2 - x1)
    y_closest = y1 + t * (y2 - y1)

    shape["x"] = x_closest - 5
    shape["y"] = y_closest
    shape["wallIndex"] = wall_index

    return shape

def find_closest_wall_index(x, y, wall_lines):
    min_distance = None
    wall_index = None

    for i, wall in enumerate(wall_lines):
        x1, y1, x2, y2 = wall["points"]
        distance = point_to_line_distance(x, y, x1, y1, x2, y2)
        if min_distance is None or distance < min_distance:
            min_distance = distance
            wall_index = i

    return wall_index

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

def extend_close_walls(wall_lines, threshold):
    for i in range(len(wall_lines)):
        x1_start, y1_start, x1_end, y1_end = wall_lines[i]["points"]
        is_horizontal_i = abs(x1_end - x1_start) > abs(y1_end - y1_start)

        for j in range(i + 1, len(wall_lines)):
            x2_start, y2_start, x2_end, y2_end = wall_lines[j]["points"]
            is_horizontal_j = abs(x2_end - x2_start) > abs(y2_end - y2_start)

            if is_horizontal_i == is_horizontal_j:
                if is_horizontal_i:
                    if abs(y1_start - y2_start) <= threshold:
                        if abs(x1_end - x2_start) <= threshold:
                            wall_lines[i]["points"][2] = x2_start
                        elif abs(x1_start - x2_end) <= threshold:
                            wall_lines[i]["points"][0] = x2_end
                        
                else:
                    if abs(x1_start - x2_start) <= threshold:
                        if abs(y1_end - y2_start) <= threshold:
                            wall_lines[i]["points"][3] = y2_start
                        elif abs(y1_start - y2_end) <= threshold:
                            wall_lines[i]["points"][1] = y2_end

    return wall_lines

def calculate_wall_angle(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1)

def remove_redundant_walls(wall_lines, proximity_threshold):
    filtered_walls = []
    skip_indices = set()

    for i in range(len(wall_lines)):
        if i in skip_indices:
            continue

        x1_start, y1_start, x1_end, y1_end = wall_lines[i]["points"]
        is_horizontal_i = abs(x1_end - x1_start) > abs(y1_end - y1_start)
        length_i = math.hypot(x1_end - x1_start, y1_end - y1_start)

        for j in range(i + 1, len(wall_lines)):
            if j in skip_indices:
                continue

            x2_start, y2_start, x2_end, y2_end = wall_lines[j]["points"]
            is_horizontal_j = abs(x2_end - x2_start) > abs(y2_end - y2_start)
            length_j = math.hypot(x2_end - x2_start, y2_end - y2_start)

            # Check for same orientation and proximity
            if is_horizontal_i == is_horizontal_j:
                if is_horizontal_i:  # For horizontal walls
                    if (abs(y1_start - y2_start) <= proximity_threshold and
                        ((x1_start <= x2_end <= x1_end) or (x2_start <= x1_end <= x2_end) or 
                         (abs(x1_start - x2_start) <= proximity_threshold or abs(x1_end - x2_end) <= proximity_threshold))):
                            # Mark the smaller or redundant wall for removal
                            if length_i >= length_j:
                                skip_indices.add(j)
                            else:
                                skip_indices.add(i)
                else:  # For vertical walls
                    if (abs(x1_start - x2_start) <= proximity_threshold and
                        ((y1_start <= y2_end <= y1_end) or (y2_start <= y1_end <= y2_end) or 
                         (abs(y1_start - y2_start) <= proximity_threshold or abs(y1_end - y2_end) <= proximity_threshold))):
                            if length_i >= length_j:
                                skip_indices.add(j)
                            else:
                                skip_indices.add(i)

        if i not in skip_indices:
            filtered_walls.append(wall_lines[i])

    return filtered_walls
