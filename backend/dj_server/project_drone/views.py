from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from django.http import HttpResponse,JsonResponse
from django.core.files.storage import FileSystemStorage
from project_drone.models import Ailogs
import datetime


# Create your views here.
@csrf_exempt
def drone_image(request):
    # request是客户端发来的请求头和数据 
    # request 是一个类的对象 有一些方式可以获得里面的数据 包括请求人的ip data等
    # query_params = request.GET.dict()  # 转换为字典
    # specific_param = request.GET.get('text')  # 获取特定参数，提供默认值
    # print(specific_param)
    uploaded_file = request.FILES.get("img")# 获取上传的文件对象                                                     
    fs=FileSystemStorage()
    fname=fs.save(uploaded_file.name,uploaded_file)
    file_url = fs.url(fname)
    aitype = request.POST.get('aitype')
    # print(aitype)
    # print(1111)
    # 获取当前北京时间，识别开始的时间
    now = datetime.datetime.now()

    # 这里是进行识别的代码

    # 获取当前北京时间，识别完成的时间

    # 时间差
    # delta_time = 两个时间相减
    ailog = Ailogs(
    aitype=1,
    imgpath=file_url,
    result=None,
    userid=666,
    dtime=now,
    delta_time=None
    )

    return JsonResponse({'image_url': file_url})

@csrf_exempt
def drone_video(request):
    uploaded_file = request.FILES.get("video")
    fs=FileSystemStorage()
    fname=fs.save(uploaded_file.name,uploaded_file)
    file_url = fs.url(fname)
    
    return JsonResponse({'video_url': file_url})