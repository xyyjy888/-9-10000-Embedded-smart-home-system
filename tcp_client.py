import socket
import sensor
import os

pipe_posture_path = r'posture'

# 只在文件被直接执行时执行的代码
if __name__ == "__main__":
    # 读取姿态识别结果
    def read_posture_from_pipe():
        with open(pipe_posture_path, 'rb') as fifo:
            data = fifo.read()
        return data.decode()

    # 客户端TCP通信初始化
    def client_tcp_init():
        global client
        print('开始连接服务器..')
        # 服务器地址和端口号 106.52.216.25 8000
        server_address = ('106.52.216.25', 8000)
        # 创建一个 TCP socket
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 连接到服务器
        client.connect(server_address)
        print('服务器连接成功')

    # 发送消息给服务器
    def client_send(message):
        global client
        client.sendall(message.encode())

    # 客户端TCP通信结束
    def client_tcp_deinit():
        global client
        print('客户端通信结束')
        # 关闭 socket 连接
        client.close()
        return 0


    client = 0

    while True:
        ser = sensor.UART_Init()  # 传感器通讯初始化, 返回串口变量
        client_tcp_init()  # tcp通讯初始化

        # 读取管道数据
        while True:
            # 读取管道数据
            pos_result = read_posture_from_pipe()
            # 通过串口读取传感器数据
            sensor_result = sensor.UART_get_sensor(ser)
            if sensor_result != -1:  # 读取到的数据正常
                if sensor_result[12] == '0':
                    os.system('sudo mpg123 fire.mp3')
                try:
                    print('客户端发送数据：' + (sensor_result.decode() + 'P:' + pos_result))
                    client_send(sensor_result.decode() + 'P:' + pos_result)
                except:
                    client_tcp_deinit()
                    break

        print('向服务器发送消息出错')
