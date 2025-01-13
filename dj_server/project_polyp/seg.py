
import json
import os
from pathlib import Path
import argparse
import cv2
import numpy as np
import onnxruntime as ort
 
# 类外定义类别映射关系，使用字典格式
CLASS_NAMES = {
    0: 'Polyp',  # 类别 0 名称
    1: 'Normal meat'   # 类别 1 名称
                       # 可以添加更多类别...
}
 
# 定义类别对应的颜色，格式为 (R, G, B)
CLASS_COLORS = {
    0: (255, 255, 0),   # 类别 0 的颜色为青黄色
    1: (255, 0, 0)      # 类别 1 的颜色为红色
                        # 可以为其他类别指定颜色...
}
 
class PolypDetection:
    def __init__(self, model_path=None):
        # 设置默认模型路径
        if model_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir,'project_polyp' , 'model', 'best.onnx')
        
        # 打印绝对路径以进行调试
        print(f"Model path: {os.path.abspath(model_path)}")
        print(f"Current working directory: {os.getcwd()}")

        # 检查文件是否存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"The model file does not exist at the specified path: {model_path}")

        self.onnx_model = model_path
        
        # 创建 Ort 推理会话，选择 CPU 或 GPU 提供者
        self.session = ort.InferenceSession(
            self.onnx_model,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
            if ort.get_device() == "GPU"
            else ["CPUExecutionProvider"],
        )
        
        # 根据 ONNX 模型类型选择 Numpy 数据类型（支持 FP32 和 FP16）
        self.ndtype = np.half if self.session.get_inputs()[0].type == "tensor(float16)" else np.single

        # 获取模型的输入宽度和高度（YOLO11-seg 只有一个输入）
        self.model_height, self.model_width = [x.shape for x in self.session.get_inputs()][0][-2:]

        # 打印模型的输入尺寸
        print("实例分割 ONNXRuntime")
        print("模型名称：", self.onnx_model)
        print(f"模型输入尺寸：宽度 = {self.model_width}, 高度 = {self.model_height}")

        # 加载类别名称
        self.classes = CLASS_NAMES

        # 加载类别对应的颜色
        self.class_colors = CLASS_COLORS


    def get_color_for_class(self, class_id):
        return self.class_colors.get(class_id, (255, 255, 255))  # 如果没有找到类别颜色，返回白色
 
    def preprocess(self, img):
        
        # 调整输入图像大小并使用 letterbox 填充
        shape = img.shape[:2]  # 原始图像大小
        new_shape = (self.model_height, self.model_width)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        ratio = r, r
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        pad_w, pad_h = (new_shape[1] - new_unpad[0]) / 2, (new_shape[0] - new_unpad[1]) / 2  # 填充宽高
        if shape[::-1] != new_unpad:  # 调整图像大小
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(pad_h - 0.1)), int(round(pad_h + 0.1))
        left, right = int(round(pad_w - 0.1)), int(round(pad_w + 0.1))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
 
        # 转换：HWC -> CHW -> BGR 转 RGB -> 除以 255 -> contiguous -> 添加维度
        img = np.ascontiguousarray(np.einsum("HWC->CHW", img)[::-1], dtype=self.ndtype) / 255.0
        img_process = img[None] if len(img.shape) == 3 else img
        return img_process, ratio, (pad_w, pad_h)
 
    def postprocess(self, preds, im0, ratio, pad_w, pad_h, conf_threshold, iou_threshold, nm=32):
        
        x, protos = preds[0], preds[1]  # 获取模型的两个输出：预测和原型
 
        # 转换维度
        x = np.einsum("bcn->bnc", x)
 
        # 置信度过滤
        x = x[np.amax(x[..., 4:-nm], axis=-1) > conf_threshold]
 
        # 合并边界框、置信度、类别和掩膜
        x = np.c_[x[..., :4], np.amax(x[..., 4:-nm], axis=-1), np.argmax(x[..., 4:-nm], axis=-1), x[..., -nm:]]
 
        # NMS 过滤
        x = x[cv2.dnn.NMSBoxes(x[:, :4], x[:, 4], conf_threshold, iou_threshold)]
 
        # 解析并返回结果
        if len(x) > 0:
            # 边界框格式转换：从 cxcywh -> xyxy
            x[..., [0, 1]] -= x[..., [2, 3]] / 2
            x[..., [2, 3]] += x[..., [0, 1]]
 
            # 缩放边界框，使其与原始图像尺寸匹配
            x[..., :4] -= [pad_w, pad_h, pad_w, pad_h]
            x[..., :4] /= min(ratio)
 
            # 限制边界框在图像边界内
            x[..., [0, 2]] = x[:, [0, 2]].clip(0, im0.shape[1])
            x[..., [1, 3]] = x[:, [1, 3]].clip(0, im0.shape[0])
 
            # 处理掩膜
            masks = self.process_mask(protos[0], x[:, 6:], x[:, :4], im0.shape)
 
            # 将掩膜转换为分割区域
            segments = self.masks2segments(masks)
            return x[..., :6], segments, masks  # 返回边界框、分割区域和掩膜
        else:
            return [], [], []
 
    @staticmethod
    def masks2segments(masks):
        
        segments = []
        for x in masks.astype("uint8"):
            c = cv2.findContours(x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]  # 找到轮廓
            if c:
                c = np.array(c[np.array([len(x) for x in c]).argmax()]).reshape(-1, 2)
            else:
                c = np.zeros((0, 2))  # 如果没有找到分割区域，返回空数组
            segments.append(c.astype("float32"))
        return segments
 
    @staticmethod
    def crop_mask(masks, boxes):
       
        n, h, w = masks.shape
        x1, y1, x2, y2 = np.split(boxes[:, :, None], 4, 1)
        r = np.arange(w, dtype=x1.dtype)[None, None, :]
        c = np.arange(h, dtype=x1.dtype)[None, :, None]
        return masks * ((r >= x1) * (r < x2) * (c >= y1) * (c < y2))
 
    def process_mask(self, protos, masks_in, bboxes, im0_shape):
       
        c, mh, mw = protos.shape
        masks = np.matmul(masks_in, protos.reshape((c, -1))).reshape((-1, mh, mw)).transpose(1, 2, 0)  # HWN
        masks = np.ascontiguousarray(masks)
        masks = self.scale_mask(masks, im0_shape)  # 将掩膜从 P3 尺寸缩放到原始输入图像大小
        masks = np.einsum("HWN -> NHW", masks)  # HWN -> NHW
        masks = self.crop_mask(masks, bboxes)  # 裁剪掩膜
        return np.greater(masks, 0.5)  # 返回二值化后的掩膜
 
    @staticmethod
    def scale_mask(masks, im0_shape, ratio_pad=None):
        
        im1_shape = masks.shape[:2]
        if ratio_pad is None:  # 计算比例
            gain = min(im1_shape[0] / im0_shape[0], im1_shape[1] / im0_shape[1])  # 比例
            pad = (im1_shape[1] - im0_shape[1] * gain) / 2, (im1_shape[0] - im0_shape[0] * gain) / 2  # 填充
        else:
            pad = ratio_pad[1]
 
        # 计算掩膜的边界
        top, left = int(round(pad[1] - 0.1)), int(round(pad[0] - 0.1))  # y, x
        bottom, right = int(round(im1_shape[0] - pad[1] + 0.1)), int(round(im1_shape[1] - pad[0] + 0.1))
        if len(masks.shape) < 2:
            raise ValueError(f'"len of masks shape" 应该是 2 或 3，但得到 {len(masks.shape)}')
        masks = masks[top:bottom, left:right]
        masks = cv2.resize(
            masks, (im0_shape[1], im0_shape[0]), interpolation=cv2.INTER_LINEAR
        )  # 使用 INTER_LINEAR 插值调整大小
        if len(masks.shape) == 2:
            masks = masks[:, :, None]
        return masks
 
    def draw_and_visualize(self, im, bboxes, segments, output_path):
        # 创建图像副本
        im_canvas = im.copy()

        for (*box, conf, cls_), segment in zip(bboxes, segments):
            # 获取类别对应的颜色
            color = self.get_color_for_class(int(cls_))

            # 绘制轮廓和填充掩膜
            cv2.fillPoly(im_canvas, np.int32([segment]), color)  # 使用类别对应的颜色填充多边形

            # 绘制边界框
            cv2.rectangle(im, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), color, 1, cv2.LINE_AA)
            # 在图像上绘制类别名称和置信度
            cv2.putText(im, f"{self.classes[cls_]}: {conf:.3f}", (int(box[0]), int(box[1] - 9)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        # 将图像和绘制的多边形混合
        im = cv2.addWeighted(im_canvas, 0.3, im, 0.7, 0)

        # 保存图像
        cv2.imwrite(str(output_path), im)

    def __call__(self, im0, conf_threshold=0.4, iou_threshold=0.45, nm=32):
        # 图像预处理
        im, ratio, (pad_w, pad_h) = self.preprocess(im0)

        # ONNX 推理
        preds = self.session.run(None, {self.session.get_inputs()[0].name: im})

        # 后处理
        boxes, segments, masks = self.postprocess(
            preds,
            im0=im0,
            ratio=ratio,
            pad_w=pad_w,
            pad_h=pad_h,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
            nm=nm,
        )
        return boxes, segments, masks

    def process_image(self, image_path):
        """
        Process the given image and save the result in the same directory.
        
        Args:
            image_path (str): Path to the input image
            
        Returns:
            tuple: A tuple containing processed image path and JSON data.
        """
        try:
            im0 = cv2.imread(image_path)
            if im0 is None:
                raise ValueError(f"无法加载图像: {image_path}")

            boxes, segments, _ = self(im0)

            output_path = Path(image_path).parent / Path(image_path).with_suffix('.result.png').name

            self.draw_and_visualize(im0, boxes, segments, output_path=output_path)
            print(f"处理后的图像已保存为 {output_path}")

            json_data = self.generate_json_result(image_path, output_path, boxes, segments)

            media_parent = Path(image_path).parent
            # 获取项目的根目录（假设 media 和 static 在同一级）
            project_root = media_parent.parent
            # 构造目标文件路径为 static 文件夹下
            static_folder = project_root / 'static'
            # 确保 static 文件夹存在
            static_folder.mkdir(parents=True, exist_ok=True)
            # 构造新的 JSON 文件路径
            json_file_name = Path(image_path).with_suffix('.json').name
            json_file_path = static_folder / json_file_name
            
            # 将 JSON 数据写入文件
            with open(json_file_path, 'w') as f:
                json.dump(json_data, f, indent=4)
                
            print(f"JSON结果已保存为 {json_file_path}")

            return str(output_path), json_data  # 返回处理后的图像路径和JSON数据
        except Exception as e:
            print(f"处理图像时发生错误: {e}")
            return None, {"error": str(e)}  # 在发生错误时返回None和错误信息

    def generate_json_result(self, original_image_path, processed_image_path, boxes, segments):
        result = {
            "original_image": str(original_image_path),
            "processed_image": str(processed_image_path),
            "detections": []
        }

        for (*box, conf, cls_), segment in zip(boxes, segments):
            detection = {
                "class": self.classes[int(cls_)],
                "confidence": float(conf),
                "bbox": [float(coord) for coord in box],
                "segmentation": [[float(point[0]), float(point[1])] for point in segment.tolist()]
            }
            result["detections"].append(detection)

        return result

    @staticmethod
    def run_from_cli(file_path=None):
        parser = argparse.ArgumentParser(description="Process an image using PolypDetection.")
        parser.add_argument("image_path", type=str, nargs='?', default="../../media/24.png",
                            help="Path to the input image. If not provided, a default image will be used.")
        
        args = parser.parse_args()
        image_path = file_path or args.image_path

        polyp_detection = PolypDetection()

        try:
            return polyp_detection.process_image(image_path)
        except Exception as e:
            print(f"处理图像时发生错误: {e}")
            return None, {"error": str(e)}

if __name__ == "__main__":
    img_path = "./media/24.png"  # 或者从命令行参数获取
    output_img_path, js_data = PolypDetection.run_from_cli(img_path)
    
   