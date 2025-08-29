import os
import main
import cv2

def handle_one(path):
    f = cv2.imread(path)
    print(path)
    main.handle_one_frame(f)
    key = cv2.waitKey(3000)


def find_images_os_walk(folder_path):
    """
    使用os.walk遍历文件夹及其子文件夹中的所有图片
    """
    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    image_paths = []
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 获取文件扩展名并转换为小写
            ext = os.path.splitext(file)[1].lower()
            if ext in image_extensions:
                full_path = os.path.join(root, file)
                # image_paths.append(full_path)
                handle_one(full_path)

    
    return image_paths

# 使用示例
folder_path = "D:\\MachineLearning\\Line2410-31-18\\image_data"
images = find_images_os_walk(folder_path)

print(f"找到 {len(images)} 张图片")
