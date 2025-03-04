# Sim-to-Real project on Unitree Go2

## 概述

此仓库以[walk-these-ways-go2](https://github.com/Teddy-Liao/walk-these-ways-go2)为基础，与RDK X5进行了适配，目前主要介绍部署部分

---
## 物料准备
|名称   | 备注   |
|------|--------|
|宇树Go2|无      |
|RDK X5|无      |
|降压模块|12-80V转5V5A，与USB接口和XT30U接口焊接在一起      |
|USB接头|![USB](media/USB.png)      |
|XT30U-M公头|![XT30U](media/XT30U.png)     |
|3D打印支架|![bracket](media/bracket.png)stl文件见bracket文件夹|
---
## 部署
已提供量化后的bin模型以及原生onnx文件，可直接运行

### 要求
#### LCM

```bash
git clone https://github.com/lcm-proj/lcm.git
mkdir build
cd build
cmake ..
make
sudo make install
```

#### Unitree_SDK2

```bash
cd go2_gym_deploy/unitree_sdk2_bin/library/unitree_sdk2
#删除编译文件
rm -r build
#编译并安装
sudo ./install.sh
mkdir build
cd build
cmake ..
make
```

### lcm_position_go2

编译lcm_position_go2并生成运行程序`lcm_position_go2`
```bash
cd go2_gym_deploy
rm -r build
mkdir build
cd build
cmake ..
make
```

### 模型推理库
```bash
git clone https://github.com/wunuo1/model_task.git -b x5
mkdir build
cd build
cmake ..
make -j4
#将编译生成的libmodel_task.so放到RDK-walk-these-ways-go2/go2_gym_deploy/scripts下
cp libmodel_task.so RDK-walk-these-ways-go2/go2_gym_deploy/scripts
```


### 验证连接
RDK X5连接Go2，测试网路连接是否正常
```bash
ping 192.168.123.161
```

查看网卡设置，确认网卡编号。我这里是eth0，用于后面启动lcm_position_go2功能
```bash
ifconfig
```

### 启动LCM
```bash
cd go2_gym_deploy/build
sudo ./lcm_position_go2 eth0
```
根据实际使用网卡替换`eth0`,启动后按`Enter`


### 加载并运行policy
打开新终端并运行
```bash
cd go2_gym_deploy/scripts
python deploy_policy_x5.py
#提供onnx运行脚本，感兴趣可以使用deploy_policy_x5_onnx.py
```
根据log的提示，按[R2]健启动控制器

### 摇杆映射

![Joystick Mapping](media/rc_map.png)

**警告**:
* 如果发生任何意外情况，请按 [L2+B] 切换到 damping 模式。
* 这是研究代码；使用风险自负；我们不对任何损坏负责。

测试效果可以参考：https://www.bilibili.com/video/BV1sW9gY1EJF/
