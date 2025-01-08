from django.db import models

# Create your models here.
class Ailogs(models.Model):
    id = models.AutoField(primary_key=True) # 自增主键 1  2  3  4  5  6  7
    imgpath = models.CharField(max_length=255, null=True, default=None) # 图片路径
    aitype = models.SmallIntegerField(default=1) # 业务类型 cnn 1 yolo 2 gan 3
    result = models.TextField(null=True, default=None) # 结果
    dtime = models.DateTimeField(auto_now_add=True) # 创建时间
    