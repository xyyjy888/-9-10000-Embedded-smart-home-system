import os
import subprocess
import time
import signal
import shutil


def start_tcp_client_process():
    processing_command = ['taskset', '-c', '0', 'python3', 'tcp_client.py']
    process = subprocess.Popen(processing_command)
    time.sleep(0.1)
    return process


def start_camera_process():
    ffmpeg_cmd = [  
        'ffmpeg',
        '-f', 'V4L2',  
        '-framerate', '30',  
        '-video_size', '640x480',  
        '-i', '/dev/video0',  
        '-bufsize', '3000k',  
        '-vcodec', 'libx264',  
        '-an',  
        '-preset:v', 'ultrafast',  
        '-tune:v', 'zerolatency',  
        '-g', '30',  
        '-maxrate', '3000k',  
        '-r', '30',  # 注意这里和最后的-r 1可能有冲突，通常用于输出帧率的-r应该只出现一次  
        '-crf', '30',  
        '-f', 'flv',  
        'rtmp://106.52.216.25/stream/wei',  
        '-fflags', 'nobuffer',  
        '-update', '1',  # 这个参数在ffmpeg的上下文中不是标准参数，可能是误加或特定用途，这里注释掉  
        '-y',   
        '-r', '1',   
        '-f', 'image2', 'out.jpg',  # 如果需要输出图片，应该单独执行这条ffmpeg命令  
    ]
    process = subprocess.Popen(ffmpeg_cmd)
    time.sleep(0.1)
    return process


def start_posture_process():
    processing_command = ['taskset', '-c', '1', 'sh', '/DEngine/run.sh', 'posture_recognition.py']
    process = subprocess.Popen(processing_command)
    time.sleep(0.1)
    return process


def start_led_process():
    processing_command = ['taskset', '-c', '0', 'python3', 'led.py']  
    process = subprocess.Popen(processing_command)
    time.sleep(0.1)
    return process

def stop_process(process):
    process.send_signal(signal.SIGINT)
    process.wait()


if __name__ == '__main__':
    print('初始化 ... ')
    folder_path = r'runs'
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    pipe_stream_path = r'camera_stream'
    pipe_posture_path = r'posture'
    if os.path.exists(pipe_stream_path):
        os.remove(pipe_stream_path)

    if os.path.exists(pipe_posture_path):
        os.remove(pipe_posture_path)

    os.mkfifo(pipe_stream_path)
    os.chmod(pipe_stream_path, 0o666)
    os.mkfifo(pipe_posture_path)
    os.chmod(pipe_posture_path, 0o666)

    print('初始化完成 ')

    tcp_client_process = None
    camera_capture_process = None
    posture_recognition_process = None
    led_process = None  # Initialize LED process

    try:
        while True:
            if tcp_client_process is None or tcp_client_process.poll() is not None:
                if tcp_client_process is not None:
                    stop_process(tcp_client_process)
                    print('tcp_client进程结束')
                tcp_client_process = start_tcp_client_process()

            if camera_capture_process is None or camera_capture_process.poll() is not None:
                if camera_capture_process is not None:
                    stop_process(camera_capture_process)
                    print('camera_capture进程结束')
                camera_capture_process = start_camera_process()

            if posture_recognition_process is None or posture_recognition_process.poll() is not None:
                if posture_recognition_process is not None:
                    stop_process(posture_recognition_process)
                    print('posture_recognition进程结束')
                posture_recognition_process = start_posture_process()

            if led_process is None or led_process.poll() is not None:
                if led_process is not None:
                    stop_process(led_process)
                    print('led进程结束')
                led_process = start_led_process()

            time.sleep(1)

    except KeyboardInterrupt:
        pass
        if tcp_client_process is not None:
            stop_process(tcp_client_process)
        if camera_capture_process is not None:
            stop_process(camera_capture_process)
        if posture_recognition_process is not None:
            stop_process(posture_recognition_process)
        if led_process is not None:
            stop_process(led_process)

    print('main程序结束')
