import serial

READ_SENSOR_DATA_CMD = b'C'
BAUDRATE = 9600
BYTESIZE = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE
PORT = '/dev/ttyS1'


# UART初始化
def UART_Init():
    try:
        ser = serial.Serial(PORT, BAUDRATE, bytesize=BYTESIZE, parity=PARITY, stopbits=STOPBITS)
        print(f"Opened serial port: {ser.name}")
    except serial.SerialException as e:
        ser = -1
        print(f"Serial error: {e}")
    # finally:
    #     if ser.isOpen():
    #         ser.close()
    #         print("Serial port closed.")
    return ser


# 串口获取传感器数据
def UART_get_sensor(ser):
    # Write command to serial port
    ser.write(READ_SENSOR_DATA_CMD)

    # Read response from serial port
    read_buf = ser.read(14)
    if len(read_buf) == 14:
        print(f"Received message: {read_buf.decode()}")
        return read_buf
    else:
        print("Get data format error")
        return -1

