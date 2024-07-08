import os
import subprocess
import time
import signal
import shutil


def start_tcp_client_process():
    processing_command = ['taskset', '-c', '1', 'python3', 'tcp_client.py']
    process = subprocess.Popen(processing_command)
    time.sleep(0.1)
    return process


def start_camera_process():
    processing_command = ['taskset', '-c', '0', 'python3', 'camera_capture.py']
    process = subprocess.Popen(processing_command)
    time.sleep(0.1)
    return process


def start_posture_process():
    processing_command = ['taskset', '-c', '1', 'python3', 'posture_recognition.py']
    process = subprocess.Popen(processing_command)
    time.sleep(0.1)
    return process


def start_led_process():
    processing_command = ['taskset', '-c', '0', 'python3', 'led.py']  # Assuming you want to run on core 2
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
        if tcp_client_process is not None:
            stop_process(tcp_client_process)
        if camera_capture_process is not None:
            stop_process(camera_capture_process)
        if posture_recognition_process is not None:
            stop_process(posture_recognition_process)
        if led_process is not None:
            stop_process(led_process)

    print('main程序结束')
