from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from django.http import HttpResponse,JsonResponse
from django.core.files.storage import FileSystemStorage
from project_drone.models import Ailogs
from project_drone.seg import PolypDetection
import datetime
import os
# Create your views here.
@csrf_exempt
def drone_image(request):
    current_time = datetime.datetime.now()
    # 
    uploaded_file = request.FILES.get("img")  # 获取上传的文件对象

    fs = FileSystemStorage()
    fname = fs.save(uploaded_file.name, uploaded_file)  # 保存文件到文件系统
    file_path = fs.path(fname)  # 获取文件的完整路径

    # 创建 PolypDetection 实例并处理图像
    output_img_path, js_data = PolypDetection.run_from_cli(file_path)
    # 使用 fs.url 方法获取输出图像的 URL
    # 注意：这里假设处理后的图像也被保存到了由 FileSystemStorage 管理的位置。
    # 如果不是，则需要确保输出图像被保存到正确的位置，并且可以通过 fs.url 访问。
    output_fname = os.path.basename(output_img_path)
    file_url = fs.url(output_fname) 
    #获取文件相对路径
    file_path = os.path.join('media', output_fname)
    current_time2=datetime.datetime.now()
    delta_time=(current_time2 - current_time).total_seconds()
    ailog = Ailogs(
        aitype=1,
        imgpath=file_path,
        result=js_data,
        dtime=current_time.strftime(r"%Y-%m-%d %H:%M:%S"),
        delta_time=delta_time,
        userid=666,
    )
    ailog.save() 
    response = {'image_url': file_url}
    return JsonResponse(response)

@csrf_exempt
def drone_video(request):
    uploaded_file = request.FILES.get("video")
    fs=FileSystemStorage()
    fname=fs.save(uploaded_file.name,uploaded_file)
    file_url = fs.url(fname)
    
    return JsonResponse({'video_url': file_url})