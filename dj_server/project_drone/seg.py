
 # Ultralytics YOLO 🚀, AGPL-3.0 license
""" 
YOLO11 分割模型 ONNXRuntime 
    功能1: 支持不用尺寸图像的输入
    功能2: 支持可视化分割结果
"""
import argparse
import datetime
import cv2
import numpy as np
import onnxruntime as ort
import os
dir_path = os.path.dirname(os.path.abspath(__file__))
_model_path=os.path.join(dir_path, "onnxmodel/best.onnx")
_model_path=os.path.relpath(_model_path)
# _img_path=os.path.join(dir_path, "model/23.png")
media_path=os.path.join(os.path.dirname(dir_path), "media")
media_path_=os.path.dirname(os.path.abspath(dir_path))
media_path=os.path.relpath(media_path)
# 类外定义类别映射关系，使用字典格式
CLASS_NAMES = {
    0: 'class_name1',  # 类别 0 名
                       # 可以添加更多类别...
}
 
# 定义类别对应的颜色，格式为 (R, G, B)
CLASS_COLORS = {
    0: (255, 255, 0),   # 类别 0 的颜色为青黄色
                        # 可以为其他类别指定颜色...
}
 
class YOLO11Seg:
    def __init__(self, onnx_model):
        # 创建 Ort 推理会话，选择 CPU 或 GPU 提供者
        self.session = ort.InferenceSession(
            onnx_model,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
            if ort.get_device() == "GPU"
            else ["CPUExecutionProvider"],
        )
        # 根据 ONNX 模型类型选择 Numpy 数据类型（支持 FP32 和 FP16）
        self.ndtype = np.half if self.session.get_inputs()[0].type == "tensor(float16)" else np.single
 
        # 获取模型的输入宽度和高度（YOLO11-seg 只有一个输入）
        self.model_height, self.model_width = [x.shape for x in self.session.get_inputs()][0][-2:]
 
        # 打印模型的输入尺寸
        print("YOLO11 🚀 实例分割 ONNXRuntime")
        print("模型名称：", onnx_model)
        print(f"模型输入尺寸：宽度 = {self.model_width}, 高度 = {self.model_height}")
 
        # 加载类别名称
        self.classes = CLASS_NAMES
 
        # 加载类别对应的颜色
        self.class_colors = CLASS_COLORS
 
    def get_color_for_class(self, class_id):
        return self.class_colors.get(class_id, (255, 255, 255))  # 如果没有找到类别颜色，返回白色
 
    def __call__(self, im0, conf_threshold=0.4, iou_threshold=0.45, nm=32):
        """
        完整的推理流程：预处理 -> 推理 -> 后处理
        Args:
            im0 (Numpy.ndarray): 原始输入图像
            conf_threshold (float): 置信度阈值
            iou_threshold (float): NMS 中的 IoU 阈值
            nm (int): 掩膜数量
        Returns:
            boxes (List): 边界框列表
            segments (List): 分割区域列表
            masks (np.ndarray): [N, H, W] 输出掩膜
        """
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
 
    def preprocess(self, img):
        """
        图像预处理
        Args:
            img (Numpy.ndarray): 输入图像
        Returns:
            img_process (Numpy.ndarray): 处理后的图像
            ratio (tuple): 宽高比例
            pad_w (float): 宽度的填充
            pad_h (float): 高度的填充
        """
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
        """
        推理后的结果后处理
        Args:
            preds (Numpy.ndarray): 来自 ONNX 的推理结果
            im0 (Numpy.ndarray): [h, w, c] 原始输入图像
            ratio (tuple): 宽高比例
            pad_w (float): 宽度的填充
            pad_h (float): 高度的填充
            conf_threshold (float): 置信度阈值
            iou_threshold (float): IoU 阈值
            nm (int): 掩膜数量
        Returns:
            boxes (List): 边界框列表
            segments (List): 分割区域列表
            masks (np.ndarray): 掩膜数组
        """
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
        """
        将掩膜转换为分割区域
        Args:
            masks (numpy.ndarray): 模型输出的掩膜，形状为 (n, h, w)
        Returns:
            segments (List): 分割区域的列表
        """
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
        """
        裁剪掩膜，使其与边界框对齐
        Args:
            masks (Numpy.ndarray): [n, h, w] 掩膜数组
            boxes (Numpy.ndarray): [n, 4] 边界框
        Returns:
            (Numpy.ndarray): 裁剪后的掩膜
        """
        n, h, w = masks.shape
        x1, y1, x2, y2 = np.split(boxes[:, :, None], 4, 1)
        r = np.arange(w, dtype=x1.dtype)[None, None, :]
        c = np.arange(h, dtype=x1.dtype)[None, :, None]
        return masks * ((r >= x1) * (r < x2) * (c >= y1) * (c < y2))
 
    def process_mask(self, protos, masks_in, bboxes, im0_shape):
        """
        处理模型输出的掩膜
        Args:
            protos (numpy.ndarray): [mask_dim, mask_h, mask_w] 掩膜原型
            masks_in (numpy.ndarray): [n, mask_dim] 掩膜数量
            bboxes (numpy.ndarray): 缩放到原始图像尺寸的边界框
            im0_shape (tuple): 原始输入图像的尺寸 (h,w,c)
        Returns:
            (numpy.ndarray): 处理后的掩膜
        """
        c, mh, mw = protos.shape
        masks = np.matmul(masks_in, protos.reshape((c, -1))).reshape((-1, mh, mw)).transpose(1, 2, 0)  # HWN
        masks = np.ascontiguousarray(masks)
        masks = self.scale_mask(masks, im0_shape)  # 将掩膜从 P3 尺寸缩放到原始输入图像大小
        masks = np.einsum("HWN -> NHW", masks)  # HWN -> NHW
        masks = self.crop_mask(masks, bboxes)  # 裁剪掩膜
        return np.greater(masks, 0.5)  # 返回二值化后的掩膜
 
    @staticmethod
    def scale_mask(masks, im0_shape, ratio_pad=None):
        """
        将掩膜缩放至原始图像大小
        Args:
            masks (np.ndarray): 缩放和填充后的掩膜
            im0_shape (tuple): 原始图像大小
            ratio_pad (tuple): 填充与原始图像的比例
        Returns:
            masks (np.ndarray): 缩放后的掩膜
        """
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
 
    def draw_and_visualize(self, im, bboxes, segments, vis=False, save=True):
        """
        绘制和可视化结果
        Args:
            im (np.ndarray): 原始图像，形状为 [h, w, c]
            bboxes (numpy.ndarray): [n, 4]，n 是边界框数量
            segments (List): 分割区域的列表
            vis (bool): 是否使用 OpenCV 显示图像
            save (bool): 是否保存带注释的图像
        Returns:
            None
        """
        # 创建图像副本
        im_canvas = im.copy()
 
        for (*box, conf, cls_), segment in zip(bboxes, segments):
            # 获取类别对应的颜色
            color = self.get_color_for_class(int(cls_))
 
            # 绘制轮廓和填充掩膜
            # cv2.polylines(im, np.int32([segment]), True, (255, 255, 255), 2)  # 绘制白色边框
            cv2.fillPoly(im_canvas, np.int32([segment]), color)  # 使用类别对应的颜色填充多边形
 
            # 绘制边界框
            cv2.rectangle(im, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), color, 1, cv2.LINE_AA)
            # 在图像上绘制类别名称和置信度
            cv2.putText(im, f"{self.classes[cls_]}: {conf:.3f}", (int(box[0]), int(box[1] - 9)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
 
        # 将图像和绘制的多边形混合
        im = cv2.addWeighted(im_canvas, 0.3, im, 0.7, 0)
 
        # 显示图像
        if vis:
            cv2.imshow("seg_result_picture", im)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        # 保存图像
        if save:
            img_name=datetime.datetime.now().time().strftime("%H%M%S")+".jpg"
            img_path=replace_digits_with_letters(img_name)
            
            img_path=os.path.join(media_path,img_path)
            img_path=os.path.relpath(img_path)
            print(img_path)
            cv2.imwrite(img_path, im)
            return img_path
def replace_digits_with_letters(s):
    """
    Replace digits 0-9 in a string with lowercase letters 'a' to 'j' respectively.
    
    :param s: Input string
    :return: Transformed string with digits replaced by letters
    """
    result = ""
    for char in s:
        if char.isdigit():
            # Replace digit with corresponding letter
            result += chr(ord('a') + int(char))
        else:
            result += char
    return result
def seg(img_path):
    # 加载模型
    model = YOLO11Seg(_model_path)
    img_path=media_path_+img_path
    # print(img_path)
    # 使用 OpenCV 读取图像
    img = cv2.imread(img_path)
    # 模型推理
    boxes, segments, _ = model(img, conf_threshold=0.5, iou_threshold=0.5)
    
    # 如果检测到目标，绘制边界框和分割区域
    if len(boxes) > 0:
        res_img_path=model.draw_and_visualize(img, boxes, segments, vis=False, save=True)
    return (res_img_path,boxes,segments)
    
# if __name__ == "__main__":
#     seg(r"/media/17.png")