import cv2
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from django.http import HttpResponse,JsonResponse
from django.core.files.storage import FileSystemStorage

# Create your views here.
# @csrf_exempt
# def drone(request):
#     # request是客户端发来的请求头和数据 
#     # request 是一个类的对象 有一些方式可以获得里面的数据 包括请求人的ip data等
#     query_params = request.GET.dict()  # 转换为字典
#     specific_param = request.GET.get('text')  # 获取特定参数，提供默认值
#     # print(specific_param)
#     uploaded_file = request.FILES.get("img")# 获取上传的文件对象                                                     
#     # print(uploaded_file)
#     fs=FileSystemStorage()
#     fname=fs.save(uploaded_file.name,uploaded_file)
#     file_url = fs.url(fname)
#     # info=[{"name":"zxx","age":200,"score":100000}]
#     return JsonResponse({'image_url': file_url})

import os

# 假设 YOLO11 类定义在 yolo11.py 文件中
from project_drone.progeress.progress import YOLO11  # 导入 YOLO11 类

@csrf_exempt
def drone(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get("img")  # 获取上传的文件对象
        
        if not uploaded_file:
            return JsonResponse({'error': 'No image uploaded'}, status=400)

        fs = FileSystemStorage()
        fname = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.path(fname)  # 获取文件的完整路径
        file_url = fs.url(fname)  # 获取文件的相对URL

        try:
            # 使用YOLO11类进行目标检测
            detection = YOLO11("./model/best.onnx", file_path, 0.5, 0.45)
            result_image_path = detection.main()

            # 将结果图像保存到相同的文件夹下
            result_image_name = f"{os.path.splitext(fname)[0]}_result{os.path.splitext(fname)[1]}"
            result_image_path_on_server = fs.path(result_image_name)
            cv2.imwrite(result_image_path_on_server, detection.postprocess(detection.img, detection.main()))

            # 构造结果图像的相对URL
            result_image_url = fs.url(result_image_name)

            return JsonResponse({
                'original_image_url': file_url,
                'result_image_url': result_image_url
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)