<template>
	<scroll-view scroll-y="true" class="chatbox" :scroll-top="y">
		<view v-for="dict in textlist" >
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
	
	<picker class="aitypechoose" mode="selector" :range="options" @change="onSelect">
		<view class="aitype">{{selectedOption}}</view>
	</picker>
</template>
<script setup>
	import {ref,nextTick} from "vue"
	const options = ['目标检测∨', 'CNN∨']
	let index=ref(0)
	let selectedOption=options[index.value]
	let y=ref(99999)
	let server_message=""
	let client_message=""
	let input_text= ref("")
	let isonlyspace= ''
	let client_image=""
	let serve_image=""
	// let video=""
	let textlist= ref([
		{ text: "您好，我是文心一言，英文名是ERNIE Bot。我能够与人对话互动，回答问题，协助创作，高效便捷地帮助人们获取信息、知识和灵感。",
		 autor: "server" ,type:"text"},
	])
	let client_send=()=> {
		if (!input_text.value.trim()) {
			return; // 防止发送空消息
		}
		textlist.value.push({ text: input_text.value, autor: "client" ,type:"text"})
		let save_input_text = input_text.value
		uni.request({
			url: 'http://127.0.0.1:8000/dj_server/', // 仅为示例，并非真实接口地址
			method: "GET",
			data: { // 文本数据被放入请求头中
				text: save_input_text
			},
			success: (res) => {
				let server_resp = res.data
				textlist.value.push({ text: server_resp, autor: "server" ,type:"text"})
				nextTick(() => {
					y.value += 1
				})
			}
		});
		input_text.value=""
	}
	let img_send=()=> {
		let type=index.value?"CNN":"OBJ"
		// 选择图片
		uni.chooseImage({
			count: 1, // 允许选择的图片数量
			success: (res) => {
				const tempFilePaths = res.tempFilePaths; // 获取图片本地文件路径列表
				const filePath = tempFilePaths[0]; // 假设只选择了一张图片
				textlist.value.push({ image: filePath, autor: "client" ,type:"image"})
				// 上传图片
				uni.uploadFile({
					url: 'http://127.0.0.1:8000/project_drone/drone_image/', // 服务器接收文件的地址
					filePath: filePath, // 要上传文件资源的路径
					name: 'img', // 文件对应的 key，开发者在服务端可以通过这个 key 获取文件数据
					formData:{aitype:type},
					
					success: (res) => {
						console.log(88888, res)
						let server_resp = JSON.parse(res.data).image_url
						// let server_resp2 = 'http://127.0.0.1:8000/project_drone/'+server_resp
						textlist.value.push({ text: "生成结果中......", autor: "server",type:"text" })
						textlist.value.push({ image: "http://127.0.0.1:8000/" + server_resp, autor: "server",type:"image" })
						nextTick(() => {
							y.value += 1
						})
					},
					fail: (err) => {
						console.error('上传失败：', err);
					}
				});
			},
			fail: (err) => {
				console.error('选择图片失败：', err);
			}
		});
	}
	let choosemp4=()=>{
		chooseVideo(["album"])
	}
	let usecamera=()=>{
		chooseVideo(["camera"])
	}
	let chooseVideo=(equipment)=> {
		uni.chooseVideo({
		  count: 1,
		  sourceType: equipment,
		  extension:["mp4","MP4"],
		  maxDuration:15,
		  success: (res) => {
			let videoFilePath = res.tempFilePath;
			// video=videoFilePath;
			console.log('选择的视频路径:', videoFilePath);
			textlist.value.push({ video: videoFilePath, autor: "client" ,type:"video"})
			uploadVideo(videoFilePath);
		  },
		  fail: (err) => {
			console.error('选择视频失败:', err);
			chooseVideo(equipment);
		  }
		});
	  }
	let uploadVideo=(filePath)=> {
		const uploadUrl = 'http://127.0.0.1:8000/project_drone/drone_video/'; // 替换为你的服务器上传接口
		uni.uploadFile({
		  url: uploadUrl,
		  filePath: filePath,
		  name: 'video', // 对应于服务器接收文件的字段名
		  success: (res) => {
			// console.log('上传成功:', res);
			// 通常服务器会返回一些数据，比如文件ID或URL
			
			let server_resp = JSON.parse(res.data).video_url
			let server_resp2 = 'http://127.0.0.1:8000/project_drone'+server_resp
			console.log(server_resp2)
			textlist.value.push({ text: "生成结果中......", autor: "server",type:"text" })
			textlist.value.push({ video: server_resp2, autor: "server",type:"video" })
			nextTick(() => {
				y.value += 1
			})
		  },
		  fail: (err) => {
			console.error('上传失败:', err);
		  }
		});
	  }
	let onLoadedMetadata=(event)=> {
	      // 视频元数据加载完成时触发
	      let videoDuration = event.detail.duration
	      console.log('视频时长:',videoDuration);
	    }
	let onSelect=(event)=>{
		index.value = event.detail.value
		// console.log(index)
		// console.log(event.detail.value)
		selectedOption = options[index.value]
	}
</script>

<style>
	.aitypechoose{
		position: fixed;
		top: 71rpx; /* 距离顶部10px */
		left: 50%;
		transform: translateX(-50%); /* 使其居中 */
		z-index: 1000; /* 保证选择框在最前面 */
		background-color: white; /* 可以自定义背景 */
		padding: 10rpx;
		border-radius: 8rpx;
		box-shadow: 0 4rpx 6rpx rgba(0, 0, 0, 0.1); /* 添加阴影效果 */
	}
	.aitype{
		text-align: center;
		font-size: 40rpx;
	}
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
	.chatbox view{
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
