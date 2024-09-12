import monkey_patch
import cv2
import subprocess
import numpy as np
from flask import Flask, render_template,url_for,jsonify
from flask_socketio import SocketIO, emit
import base64
from flask_cors import CORS
import os
import json



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")


# FFmpeg 命令来接收 RTMP 流并输出为原始数据格式
FFMPEG_COMMAND = [
    'ffmpeg',
    '-i', 'rtmp://localhost/hls/room8',
    '-f', 'image2pipe',
    '-pix_fmt', 'bgr24',  # OpenCV 需要使用 bgr24
    '-vcodec', 'rawvideo', '-'
]

def generate_frames():
    # 使用 subprocess 启动 FFmpeg 进程
    process = subprocess.Popen(FFMPEG_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    width = 720
    height = 1280
    frame_size = width * height * 3  # 每帧图像的大小 (RGB/BGR)

    while True:
        # 从 FFmpeg 管道中读取视频帧数据
        raw_frame = process.stdout.read(frame_size)
        if len(raw_frame) != frame_size:
            break  # 读取的数据不足，停止
        # 将原始字节数据转换为 NumPy 数组并重构为图像
        frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
        _, buffer = cv2.imencode('.jpg', frame)
        frame_data = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('video_frame', {'frame': frame_data})
        socketio.sleep(0.03)  # 控制帧率

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/video')
def video():
    return render_template('video.html')
@app.route('/analysis')
def analysis():
    return render_template('analysis.html')
@app.route('/information')
def information():
    return render_template('information.html')
@app.route('/question')
def question():
    return render_template('question.html')

@socketio.on('connect')
def connect():
    print("Client connected")
    socketio.start_background_task(generate_frames)
@app.route('/get_images1')
def get_images1():
    image_folder = os.path.join(app.static_folder, "img/carouselChart1")
    images = [f"static/img/carouselChart1/{img}" for img in os.listdir(image_folder) if img.endswith((".png", ".jpg", ".jpeg", ".gif"))]
    return jsonify(images)  # 返回图片的路径列表（JSON 格式）
@app.route('/get_images2')
def get_images2():
    image_folder = os.path.join(app.static_folder, "img/carouselChart2")
    images = [f"static/img/carouselChart2/{img}" for img in os.listdir(image_folder) if img.endswith((".png", ".jpg", ".jpeg", ".gif"))]
    return jsonify(images)  # 返回图片的路径列表（JSON 格式）


@app.route('/get_chart_data')
def get_chart_data():
    with open('jiaotong_data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    total_count = len(data)
    damaged_count = sum(1 for item in data if item['is_damaged'] == 1)
    undamaged_count = total_count - damaged_count

    # 统计每种物品的损坏和未损坏数量
    item_stats = {}
    for item in data:
        name = item['name']
        if name not in item_stats:
            item_stats[name] = {'damaged': 0, 'undamaged': 0}
        if item['is_damaged'] == 1:
            item_stats[name]['damaged'] += 1
        else:
            item_stats[name]['undamaged'] += 1

    # 计算损坏和未损坏占总数的百分比
    pass_rate_data = {
        'labels': ['合格', '故障'],
        'data': [undamaged_count / total_count * 100, damaged_count / total_count * 100]
    }

    # 计算损坏物品占所有损坏数的比例
    fault_distribution_data = {
        'labels': list(item_stats.keys()),
        'data': [item_stats[name]['damaged'] / damaged_count * 100 for name in item_stats]
    }

    # 计算损坏的数量
    faults_bar_data = {
        'labels': list(item_stats.keys()),
        'data': [item_stats[name]['damaged'] for name in item_stats]
    }

    return jsonify({
        'pass_rate_data': pass_rate_data,
        'fault_distribution_data': fault_distribution_data,
        'faults_bar_data': faults_bar_data
    })

if __name__ == '__main__':
    print(f"Running on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)