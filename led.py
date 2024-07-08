import smbus
import os
import time

period = 256000
dutycycle = 0


def dbmsg(msg):
    print(f"{msg}")


# pwm初始化
def pwm_setup():
    # Export PWM0 if not already exported
    if not os.path.exists("/sys/class/pwm/pwmchip0/pwm0"):
        try:
            with open("/sys/class/pwm/pwmchip0/export", "w") as export_file:
                export_file.write("0")
            # dbmsg("export pwm0 ok")
        except IOError:
            dbmsg("open export error")
            return -1

    # Open PWM files
    try:
        fd_period = open("/sys/class/pwm/pwmchip0/pwm0/period", "w")
        fd_duty = open("/sys/class/pwm/pwmchip0/pwm0/duty_cycle", "w")
        # print('fd_duty : ', fd_duty)
        fd_enable = open("/sys/class/pwm/pwmchip0/pwm0/enable", "w")
    except IOError:
        dbmsg("open error")
        return -1

    # Set period
    try:
        fd_period.write(str(int(period)))
        # dbmsg("change period ok")
    except IOError:
        dbmsg("change period error")
        return -1

    # Set initial duty cycle
    try:
        fd_duty.write(str(dutycycle))
        # dbmsg("change duty_cycle ok")
    except IOError:
        dbmsg("change duty_cycle error")
        return -1

    # Enable PWM
    # print('fd_enable : ', fd_enable)
    try:
        fd_enable.write(str(1))
        # dbmsg("enable pwm0 ok")
    except IOError:
        dbmsg("enable pwm0 error")
        return -1

    return fd_duty  # 返回文件对象


# 只在文件被直接执行时执行的代码
if __name__ == "__main__":
    # 设定 I2C 总线号和设备地址
    bus = smbus.SMBus(0)
    address = 0x48  # AD转换模块的 I2C 地址

    # 初始化PWM
    fd_duty = pwm_setup()
    if fd_duty is None:
        dbmsg("PWM 设置失败，退出。")
        exit(1)
    last_pwm_duty = 1

    dbmsg('智能灯光开启')

    try:
        while True:
            # 读取光照数据
            light_ad_value = bus.read_byte_data(address, 0)
            # 处理光敏电阻AD值
            # pwm_duty 指低电平占空比
            if light_ad_value < 100:
                pwm_duty = 1  # LED不亮
            elif light_ad_value > 160:
                pwm_duty = 0  # LED最亮
            else:
                pwm_duty = (160 - light_ad_value) / 60
            # 若占空比改变
            if pwm_duty != last_pwm_duty:
                os.write(fd_duty.fileno(), bytes(str(int(period * pwm_duty)), 'utf-8'))
                last_pwm_duty = pwm_duty
                time.sleep(1)

    except KeyboardInterrupt:
        # 关闭总线
        bus.close()
        # 关闭PWM
        if os.path.exists("/sys/class/pwm/pwmchip0/pwm0"):
            # print('unexport pwm0...')
            try:
                os.write(fd_duty.fileno(), bytes(str(int(period)), 'utf-8'))
                with open("/sys/class/pwm/pwmchip0/unexport", "w") as unexport_file:
                    unexport_file.write("0")
                dbmsg("unexport pwm0 ok")
            except IOError:
                dbmsg("open unexport error")
