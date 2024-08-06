import sys
import numpy as np
import time
import cv2
import os
import signal
import de
from infer_engine import InferEngine
import time

pipe_stream_path = r'camera_stream'
pipe_posture_path = r'posture'


# 函数用于将识别写入命名管道
def write_result_to_pipe(my_result_posture):
    with open(pipe_posture_path, 'wb') as fifo:
        fifo.write(my_result_posture.encode())
        fifo.flush()


def xywh2xyxy(x):
    # [x, y, w, h] to [x1, y1, x2, y2]
    y = np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2
    y[:, 1] = x[:, 1] - x[:, 3] / 2
    y[:, 2] = x[:, 0] + x[:, 2] / 2
    y[:, 3] = x[:, 1] + x[:, 3] / 2
    return y


def py_cpu_nms(dets, thresh):
    x = dets[:, 0]
    y = dets[:, 1]
    w = dets[:, 2]
    h = dets[:, 3]
    x1 = x - w / 2 + 1
    y1 = y - h / 2 + 1
    x2 = x + w / 2
    y2 = y + w / 2
    scores = dets[:, 4]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    res = []
    index = scores.argsort()[::-1]
    while index.size > 0:
        i = index[0]
        res.append(i)
        x11 = np.maximum(x1[i], x1[index[1:]])
        y11 = np.maximum(y1[i], y1[index[1:]])
        x22 = np.minimum(x2[i], x2[index[1:]])
        y22 = np.minimum(y2[i], y2[index[1:]])

        w = np.maximum(0, x22 - x11 + 1)
        h = np.maximum(0, y22 - y11 + 1)

        overlaps = w * h
        iou = overlaps / (areas[i] + areas[index[1:]] - overlaps)

        idx = np.where(iou <= thresh)[0]
        index = index[idx + 1]
    return np.array(res, dtype=np.int32)


def filter_box(org_box, conf_thres, iou_thres):  # 过滤掉无用的框
    # -------------------------------------------------------
    #   删除为1的维度
    #	删除置信度小于conf_thres的BOX
    # -------------------------------------------------------
    org_box = np.squeeze(org_box)
    conf = org_box[..., 4] > conf_thres
    box = org_box[conf == True]
    # -------------------------------------------------------
    #	通过argmax获取置信度最大的类别
    # -------------------------------------------------------
    cls_cinf = box[..., 5:]
    cls = []
    for i in range(len(cls_cinf)):
        cls.append(int(np.argmax(cls_cinf[i])))
    all_cls = list(set(cls))
    # -------------------------------------------------------
    #   分别对每个类别进行过滤
    #	1.将第6列元素替换为类别下标
    #	2.xywh2xyxy 坐标转换
    #	3.经过非极大抑制后输出的BOX下标
    #	4.利用下标取出非极大抑制后的BOX
    # -------------------------------------------------------
    output = []
    for i in range(len(all_cls)):
        curr_cls = all_cls[i]
        curr_cls_box = []
        curr_out_box = []
        for j in range(len(cls)):
            if cls[j] == curr_cls:
                box[j][5] = curr_cls
                curr_cls_box.append(box[j][:6])
        curr_cls_box = np.array(curr_cls_box)
        # curr_cls_box_old = np.copy(curr_cls_box)
        curr_cls_box = xywh2xyxy(curr_cls_box)
        curr_out_box = py_cpu_nms(curr_cls_box, iou_thres)
        for k in curr_out_box:
            output.append(curr_cls_box[k])
    output = np.array(output)
    return output

# 只在文件被直接执行时执行的代码
if __name__ == "__main__":
    # 加载模型
    # model = YOLO(r'best.pt')  # 预训练的 YOLOv8n 模型
    print("InferEngine example start...")
    net_file = "/DEngine/model/posture/net.bin"
    model_file = "/DEngine/model/posture/model.bin"
    engine = InferEngine(net_file, model_file, max_batch=1)

    format = de.PixelFormat.DE_PIX_FMT_RGB888_PLANE
    CLASSES = ('normal', 'hunchback', 'recline')

    last_played_time = time.time()

    print('姿态推理开始')

    def signal_handler(sig, frame):  
        engine.profile()
        # 调用sys.exit()来退出程序  
        sys.exit(0)  
  
    # 注册SIGINT信号的处理函数  
    signal.signal(signal.SIGINT, signal_handler) 

    while True:
        # 使用模型进行推理
        frame = cv2.imread('out.jpg')

        frame = cv2.resize(frame, (640, 640))
        img = frame[:, :, ::-1].transpose(2, 0, 1)  # BGR2RGB和HWC2CHW
        img = np.expand_dims(img, axis=0)
        # Run the model on the pre-processed frame
        shape = (1, 3, 640, 640)
        data = [(format, shape, img)]

        t1 = time.time()
        output = engine.predict(data)
        t2 = time.time()
        print('该帧算法处理耗时 :  %.4f seconds.' % (t2-t1))

        output = output[0]
        outbox = filter_box(output, 0.6, 0.5)

        # print('该帧算法处理结果 : ', outbox)
 
        if outbox.size > 0 :  # 结果列表不为空
            for o in outbox:
                x1 = str(int(o[0]))
                y1 = str(int(o[1]))
                x2 = str(int(o[2]))
                y2 = str(int(o[3]))
                score = o[4]
                classes = int(o[5])

                text = "%s:%.2f" % (CLASSES[classes], score)

                print('类别 : ', text)
                cls = str(classes + 1)
                break
        else:
            print('未识别到')
            cls = '0'  # 0 - 未识别到
            x1 = '0'
            y1 = '0'
            x2 = '0'
            y2 = '0'

        ans = 'P:' + cls + ';' + 'x:' + x1 + ';' + 'y:' + y1 + ';' + 'z:' + x2 + ';' + 'w:' + y2 + ';'

        write_result_to_pipe(ans)
        # 播放提醒音频
        if cls == '2' and time.time() - last_played_time > 3:  # 驼背
            last_played_time = time.time()                    
            os.system('mpg123 hunchback.mp3')
        elif cls == '3' and time.time() - last_played_time > 3:  # 后仰
            last_played_time = time.time()
            os.system('mpg123 hypsokinesis.mp3')


