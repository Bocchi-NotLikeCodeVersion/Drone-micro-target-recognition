import os
import shutil
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
import tqdm
# 路径设置
datasets_folder = 'datasets'
original_images_folder = os.path.join(datasets_folder, 'images')
original_masks_folder = os.path.join(datasets_folder, 'masks')

# 创建训练和验证集的文件夹结构
train_folder = os.path.join(datasets_folder, 'train')
val_folder = os.path.join(datasets_folder, 'val')

for folder in [train_folder, val_folder]:
    for subdir in ['images', 'labels']:
        os.makedirs(os.path.join(folder, subdir), exist_ok=True)

# 获取所有图像和掩码文件名（不包括扩展名）
image_filenames = set(os.path.splitext(f)[0] for f in os.listdir(original_images_folder))
mask_filenames = set(os.path.splitext(f)[0] for f in os.listdir(original_masks_folder))

# 取交集，确保图像和掩码文件配对存在
filenames = image_filenames.intersection(mask_filenames)

# 划分数据集
train_filenames, val_filenames = train_test_split(list(filenames), test_size=0.2, random_state=42)

# 处理训练和验证集
for filenames_set, target_folder in [(train_filenames, train_folder), (val_filenames, val_folder)]:
    for filename in filenames_set:
        # 处理图像文件
        image_src_path = os.path.join(original_images_folder, filename + '.png')
        image_dst_path = os.path.join(target_folder, 'images', filename + '.png')
        shutil.copy2(image_src_path, image_dst_path)
        
        # 处理掩码文件并生成标签
        mask_src_path_png = os.path.join(original_masks_folder, filename + '.png')
        mask_src_path_bmp = os.path.join(original_masks_folder, filename + '.bmp')
        
        if os.path.exists(mask_src_path_png):
            mask = cv2.imread(mask_src_path_png, cv2.IMREAD_GRAYSCALE)
            mask_src_path = mask_src_path_png
        elif os.path.exists(mask_src_path_bmp):
            mask = cv2.imread(mask_src_path_bmp, cv2.IMREAD_GRAYSCALE | cv2.IMREAD_IGNORE_ORIENTATION)
            mask_src_path = mask_src_path_bmp
        else:
            print(f"No mask file found for {filename}")
            continue
        
        if mask is None:
            print(f"Failed to load mask: {mask_src_path}")
            continue
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        label_dst_path = os.path.join(target_folder, 'labels', filename + '.txt')
        
        with open(label_dst_path, 'w') as f:
            for contour in contours:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                image = cv2.imread(image_dst_path)
                height, width = image.shape[:2]
                yolo_coords = []
                for point in approx:
                    x, y = point[0]  # 修复方式：从二维数组中提取坐标
                    yolo_coords.extend([x / width, y / height])
                
                f.write(f'0 {" ".join(map(str, yolo_coords))}\n')

print("训练和验证集已生成！")