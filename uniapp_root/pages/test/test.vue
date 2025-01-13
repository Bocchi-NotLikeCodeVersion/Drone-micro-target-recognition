<template>
	<scroll-view scroll-y="true" class="chatbox" :scroll-top="y">
		<view v-for="dict in textlist">
			<view v-if="dict.autor === 'server'&& dict.type ==='text'" class="left_message">
				<image class="head" src="../../static/chat/AI.png" mode=""></image>
				<rich-text :nodes="dict.text"></rich-text>
			</view>
			<view v-else-if="dict.autor === 'client' && dict.text !== ''&& dict.type ==='text'" class="right_message">
				<rich-text :nodes="dict.text"></rich-text>
				<image class="head" src="../../static/chat/user.jpg" mode=""></image>
			</view>
			<!-- image -->
			<view v-if="dict.autor === 'server'&& dict.type ==='image'" class="left_message">
				<image class="head" src="../../static/chat/AI.png" mode=""></image>
				<image class="image_message" :src="dict.image" mode=""></image>
			</view>
			<view v-else-if="dict.autor === 'client' && dict.text !== ''&& dict.type ==='image'" class="right_message">
				<image class="image_message" :src="dict.image" mode=""></image>
				<image class="head" src="../../static/chat/user.jpg" mode=""></image>
			</view>
			<!-- video -->
			<view v-if="dict.autor === 'server'&& dict.type ==='video'" class="left_message">
				<image class="head" src="../../static/chat/AI.png" mode=""></image>
				<video :src="dict.video" class="video_message" controls></video>
			</view>
			<view v-else-if="dict.autor === 'client' && dict.text !== ''&& dict.type ==='video'" class="right_message">
				<video @loadedmetadata="onLoadedMetadata" :src="dict.video" class="video_message" controls></video>
				<image class="head" src="../../static/chat/user.jpg" mode=""></image>
			</view>

		</view>

	</scroll-view>

	<view class="inputbox">
		<textarea ref="inputarea" class="inputarea" v-model="input_text" placeholder=""></textarea>
		<button @click="client_send">发送</button>
	</view>

	<view class="selectbox">
		<image src="../../static/chat/image.png" @click="img_send" mode=""></image>
		<image src="../../static/chat/photo.png" @click="usecamera" mode=""></image>
		<image src="../../static/chat/video.png" @click="chooseVideo" mode=""></image>
		<image src="../../static/chat/加号.png" mode=""></image>
	</view>
</template>

<script setup>
	import {
		ref,
		nextTick
	} from "vue";

	let y = ref(99999);
	let input_text = ref("");
	let textlist = ref([{
		text: "您好，我是文心一言，英文名是ERNIE Bot。我能够与人对话互动，回答问题，协助创作，高效便捷地帮助人们获取信息、知识和灵感。",
		autor: "server",
		type: "text"
	}]);
	let client_send = () => {
		if (!input_text.value.trim()) {
			return; // 防止发送空消息
		}
		textlist.value.push({
			text: input_text.value,
			autor: "client",
			type: "text"
		})
		let save_input_text = input_text.value
		uni.request({
			url: 'http://127.0.0.1:8000/dj_server/', // 仅为示例，并非真实接口地址
			method: "GET",
			data: { // 文本数据被放入请求头中
				text: save_input_text
			},
			success: (res) => {
				let server_resp = res.data
				textlist.value.push({
					text: server_resp,
					autor: "server",
					type: "text"
				})
				nextTick(() => {
					y.value += 1
				})
			}
		});
		input_text.value = ""
	};
	let drawBoxOnImage = (imageUrl, boxes) => {
	  return new Promise((resolve, reject) => {
	    const canvas = document.createElement('canvas');
	    const ctx = canvas.getContext('2d');
	    const img = new Image();
	    img.crossOrigin = "anonymous"; // 设置跨域属性以加载外部图片
	    img.src = imageUrl;
	    img.onload = () => {
	      // 设置画布大小与图片一致
	      canvas.width = img.width;
	      canvas.height = img.height;
	
	      // 绘制原始图片
	      ctx.drawImage(img, 0, 0);
	
	      // 定义边框的颜色和线宽
	      const borderColor = '#FF0000'; // 红色边框
	      const borderWidth = 2; // 边框宽度
	
	      // 根据传入的boxes数组绘制边框
	      boxes.forEach(box => {
	        const [x, y, width, height] = box; // 解构赋值
	        ctx.lineWidth = borderWidth;
	        ctx.strokeStyle = borderColor;
	        ctx.strokeRect(x, y, width, height);
	      });
	
	      // 将绘制好的canvas转换为新的图片URL
	      resolve(canvas.toDataURL('image/png'));
	    };
	    img.onerror = reject;
	  });
	};
	
	// 修改后的img_send函数
	let img_send = async () => {
	  try {
	    // 选择图片并显示预览
	    const res = await new Promise((resolve, reject) => {
	      uni.chooseImage({
	        count: 1,
	        success: resolve,
	        fail: error => {
	          console.error('选择图片失败:', error);
	          reject(error);
	        }
	      });
	    });
	
	    const tempFilePaths = res.tempFilePaths;
	    if (tempFilePaths.length === 0) {
	      console.error('没有选择图片');
	      return;
	    }
	
	    const filePath = tempFilePaths[0];
	    textlist.value.push({ image: filePath, autor: "client", type: "image" });
	    console.log('选择了图片:', filePath);
	
	    // 显示正在上传的消息
	    textlist.value.push({ text: "图片上传中...", autor: "server", type: "text" });
	
	    // 上传图片，设置合理的超时时间
	    const uploadRes = await new Promise((resolve, reject) => {
	      uni.uploadFile({
	        url: 'http://127.0.0.1:8000/project_drone/drone_image/',
	        filePath,
	        timeout: 16000, // 设置16秒超时时间
	        name: 'img',
	        success: resolve,
	        fail: error => {
	          console.error('上传图片失败:', error);
	          reject(error);
	        }
	      });
	    });
	
	    let server_resp = JSON.parse(uploadRes.data);
	    console.log('服务器响应:', server_resp);
	    
	    if (!server_resp.image_url || !server_resp.result) {
	      throw new Error('服务器返回的数据不完整');
	    }
	
	    let server_resp2 = `http://127.0.0.1:8000/project_drone${server_resp.image_url}`;
	    console.log('完整的图片URL:', server_resp2);
	    
	    // 更新消息列表中的文本
	    textlist.value.pop(); // 移除“图片上传中...”
	    textlist.value.push({ text: "生成结果中......", autor: "server", type: "text" });
	
	    // 使用drawBoxOnImage绘制边框，并更新消息列表中的图片
	    const boxedImageUrl = await drawBoxOnImage(server_resp2, server_resp.result.boxes || []);
	    textlist.value.push({ image: boxedImageUrl, autor: "server", type: "image" });
	
	    nextTick(() => {
	      y.value += 1;
	    });
	
	  } catch (error) {
	    console.error('处理图片时发生错误：', error);
	    textlist.value.push({ text: "处理图片时发生错误，请稍后再试。", autor: "server", type: "text" });
	  }
	};
	let choosemp4 = () => {
		chooseVideo(["album"])
	}
	let usecamera = () => {
		chooseVideo(["camera"])
	}
	let chooseVideo = (equipment) => {
		uni.chooseVideo({
			count: 1,
			sourceType: equipment,
			extension: ["mp4", "MP4"],
			maxDuration: 15,
			success: (res) => {
				let videoFilePath = res.tempFilePath;
				// video=videoFilePath;
				console.log('选择的视频路径:', videoFilePath);
				textlist.value.push({
					video: videoFilePath,
					autor: "client",
					type: "video"
				})
				uploadVideo(videoFilePath);
			},
			fail: (err) => {
				console.error('选择视频失败:', err);
				chooseVideo(equipment);
			}
		});
	}
	let uploadVideo = (filePath) => {
		const uploadUrl = 'http://127.0.0.1:8000/project_drone/drone_video/'; // 替换为你的服务器上传接口
		uni.uploadFile({
			url: uploadUrl,
			filePath: filePath,
			name: 'video', // 对应于服务器接收文件的字段名
			success: (res) => {
				// console.log('上传成功:', res);
				// 通常服务器会返回一些数据，比如文件ID或URL
				let server_resp = JSON.parse(res.data).video_url
				let server_resp2 = 'http://127.0.0.1:8000/project_drone' + server_resp
				console.log(server_resp2)
				textlist.value.push({
					text: "生成结果中......",
					autor: "server",
					type: "text"
				})
				textlist.value.push({
					video: server_resp2,
					autor: "server",
					type: "video"
				})
				nextTick(() => {
					y.value += 1
				})
			},
			fail: (err) => {
				console.error('上传失败:', err);
			}
		});
	}
	let onLoadedMetadata = (event) => {
		// 视频元数据加载完成时触发
		let videoDuration = event.detail.duration
		console.log('视频时长:', videoDuration);
	}
</script>
<style>
	.chatbox {
		height: 1000rpx;
		width: 750rpx;
		background-color: #e6e6e6;

	}

	.left_message {
		display: flex;
		flex-flow: row nowrap;
		justify-content: left;
	}

	.right_message {
		display: flex;
		flex-flow: row nowrap;
		justify-content: right;
	}

	.chatbox view .image_message {
		/* height: 600rpx;
		width: 600rpx; */
		/* border-radius: 100rpx; */
	}

	.chatbox view {
		padding: 10rpx;
	}

	.chatbox view .head {
		height: 100rpx;
		width: 100rpx;
		border-radius: 100rpx;
	}

	.chatbox view rich-text {
		background-color: #fcfcfc;
		border-radius: 10rpx;
		line-height: 70rpx;
		padding: 10rpx;
		margin: 10rpx;
		max-width: 550rpx;
	}

	.inputbox {
		height: 100rpx;
		width: 750rpx;
		background-color: #eeeeee;
		display: flex;
		flex-flow: row nowrap;
		align-items: center;
	}

	.inputbox button {
		height: 90rpx;
		background-color: #2bbfeb;
		font-size: 30rpx;
		text-align: center;
		line-height: 90rpx;
		color: #101010;
		opacity: 0.8;
	}

	.inputarea {
		width: 600rpx;
		background-color: #ffffff;
		border-radius: 15rpx;
		height: 90rpx;
		line-height: 90rpx;
	}

	.selectbox {
		height: 50rpx;
		width: 750rpx;
		background-color: #eeeeee;
		display: flex;
		flex-flow: row nowrap;
		justify-content: space-around;
	}

	.selectbox image {
		height: 50rpx;
		width: 50rpx;
		opacity: 0.6;
	}
</style>