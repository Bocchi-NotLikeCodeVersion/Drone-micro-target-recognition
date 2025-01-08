from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from django.http import HttpResponse,JsonResponse
from django.core.files.storage import FileSystemStorage

# Create your views here.
@csrf_exempt
def drone(request):
    # request是客户端发来的请求头和数据 
    # request 是一个类的对象 有一些方式可以获得里面的数据 包括请求人的ip data等
    query_params = request.GET.dict()  # 转换为字典
    specific_param = request.GET.get('text')  # 获取特定参数，提供默认值
    # print(specific_param)
    uploaded_file = request.FILES.get("img")# 获取上传的文件对象                                                     
    # print(uploaded_file)
    fs=FileSystemStorage()
    fname=fs.save(uploaded_file.name,uploaded_file)
    file_url = fs.url(fname)
    # info=[{"name":"zxx","age":200,"score":100000}]
    return JsonResponse({'image_url': file_url})