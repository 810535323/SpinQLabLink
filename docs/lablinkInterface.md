# Lab 主副软件通信协议规范

## 协议概述
1. 使用TCP Socket长连接
2. 连接建立后需立即完成登录认证
3. 二进制报文采用固定头+Protobuf载荷格式

## 报文格式
| 头部标识 (4B)       | 长度字段 (大端序 4B) | 实际 Protobuf 数据 (nB) |
|---------------------|-----------------------|-------------------------|
| `0xCAFEBABE`            | 长度值（二进制）      | 序列化的二进制数据      |

| 字段                | 描述                                                                 |
|---------------------|---------------------------------------------------------------------|
| **头部标识** `0xCAFEBABE` | 固定 4 字节，标识数据包类型                                         |
| **长度字段**         | 大端序 4 字节，表示后续 Protobuf 数据的长度（单位：字节）           |
| **Protobuf 数据**    | 根据协议定义的 `.proto` 文件序列化后的二进制数据，长度由长度字段决定 |



## Protobuf格式：
```protobuf
syntax = "proto3";

message BaseMessage {
  Metadata metadata = 1;
  string msg_id = 2; // 消息类型：用来区分不同的业务操作

  // 使用oneof，表示使用其中一种格式进行传输
  oneof message_type {
    ChartData chart_data = 33; // 谱线数据格式
    string json_data = 44; // json字符串格式
  } 
}

/**
* 每条报文都需要的报文数据
*/
message Metadata {
  int64 sequence_id = 1; // 主动类型的消息需要创建唯一的消息ID，如果是应答消息，必须把请求消息数据包中的这个字段返回，以形成闭环
  int64 timestamp = 2; // 消息的时间戳
  string account = 4; // 发送消息的用户名称
  string session_id = 5;// 登录得到的会话id
}

/**
* 谱线数据
*/
message ChartData {
  string task_id = 1; // 所属任务id
  string group = 2; // 所属实验
  string chart_name = 3; // 图表名称
  optional string path=4; // 图表通道
  optional string qubit =5; // 图表比特？三比特有，后续扩展
  optional string step = 6; // 观测步骤
  repeated DataPointProto points = 7;
}

message DataPointProto {
  float x = 1;
  float y = 2;
}
```

## 消息类型（msg_id)规范:

| **前缀**                | **说明**   | **示例**   |
|---------------------|----------------|-----------|
| "c_" | 客户端主动发送   |c_user_login_req|
| "s_" | 服务端端主动发送   |s_post_device_info|

| **后缀**                | **说明**   | **示例**   |
|---------------------|----------------|-----------|
| "_req" | 请求消息   |c_user_login_req|
| "_res" | 响应消息   |s_user_login_res|

其它结尾的消息为单向消息，无对应响应消息；

## 消息列表
### 心跳包
- **"heartbeat_req"** 
    说明：客户端发送心跳包
    报文体：
    ```json
     "{}" 
     ```

- **"heartbeat_res"** 
    说明：服务端响应心跳包
    报文体：
    ```json
    "{}"
    ```

### 登录
- **"c_user_login_req"** 
    说明：客户端登录请求
    报文体：
    ```json
    "{\"account\":\"Lab-746181000\",\"password\":\"123456\"}"
     ```

- **"s_user_login_res"** 
    说明：服务端登录请求
    报文体1：
    ```json
    "{\"sessionId\":\"a738e400aec2d9161268459f599e9cd78ce0bc3b6566c61632271208e539660d\",\"code\":0,\"message\":\"Success\"}"
     ```
    报文体2：
    ```json
    "{\"code\":998,\"message\":\"Reapet Login\"}"
    ```
    报文体3：
    ```json
    "{\"code\":999,\"message\":\"Unknow error\"}"
    ```

### 设备状态更新
- **"s_post_device_info"** 
    说明：服务端主动发送设备信息(主板连接状态、锁场状态、温度)
    发送时机：随温度定时更新、主板连接状态变化、锁场状态变化
    报文体：
    ```json
    "{\"connected\":true,\"lockState\":true,\"temperature\":20.757}"
    ```

- **"s_post_device_param"** 
    说明：服务端主动发送设备参数
    发送时机：登录成功后、主机从仪器调试界面退出（无论是否真正修改过参数）
    报文体：
    ```json
    "{\"currentShimming\":1.5051086,\"lockParam\":{\"fre_offset\":\"1407\",\"lock_factor\":\"4000\"},\"ppsParam\":{\"Hmeasure\":\"0\",\"Q1ResonantFrequency\":\"0\",\"Q1_Mod\":\"-1\",\"Q1_Mod1\":\"9242179\",\"Q1_Mod2\":\"9242179\",\"Q1_lamda1\":\"28.87\",\"Q1_lamda2\":\"3.814\",\"Q1_lamdaNoise\":\"0\",\"Q1_noise\":\"37045.4648\",\"Q1_ratio\":\"-0.292\",\"Q2ResonantFrequency\":\"0\",\"Q2_Mod\":\"-1\",\"Q2_Mod1\":\"282436\",\"Q2_Mod2\":\"282436\",\"Q2_lamda1\":\"29.562\",\"Q2_lamda2\":\"29.562\",\"Q2_noise\":\"1526.621\",\"Q2_ratio\":\"3.899\",\"Q3ResonantFrequency\":\"0\",\"Q3_Mod\":\"-1\",\"Q3_lamda1\":\"-1\",\"Q3_lamda2\":\"-1\",\"Q3_noise\":\"0\",\"Q3_ratio\":\"-1\",\"am_Q1\":\"39.473\",\"am_Q2\":\"47.134\",\"d_time\":\"250\",\"j_time\":\"720\",\"noise\":\"0\",\"relax_time\":\"15\",\"repeat_n\":\"5\",\"t2_1\":\"200\",\"t2_2\":\"200\",\"t2_3\":\"0\",\"width_Q1\":\"40\",\"width_Q2\":\"40\"},\"pulseParam\":{\"Q1_freOffset\":\"-10\",\"Q2_freOffset\":\"10\",\"am_Lock\":\"80\",\"am_Q1\":\"33\",\"am_Q2\":\"50\",\"estimatedFreq_Lock\":\"21000000.000000\",\"estimatedFreq_Q1\":\"21000000.000000\",\"estimatedFreq_Q2\":\"9000000.000000\",\"f_Lock\":\"2.1170853918E7\",\"f_Q1\":\"2.25035473405E7\",\"f_Q2\":\"9109648.4953\",\"freqProtection_Lock\":\"0\",\"freqProtection_Q1\":\"0\",\"freqProtection_Q2\":\"0\",\"limitationFreq_Lock\":\"5000000.000000\",\"limitationFreq_Q1\":\"5000000.000000\",\"limitationFreq_Q2\":\"5000000.000000\",\"phase0_Q1\":\"0\",\"phase0_Q2\":\"0\",\"phase0_Q3\":\"0\",\"phase1\":\"0\",\"phaseQ1_0\":\"227.5\",\"phaseQ1_1\":\"10\",\"phaseQ2_0\":\"204.9\",\"phaseQ2_1\":\"0\"},\"sampleParam\":{\"fft_end_Lock\":\"8000\",\"fft_end_Q1\":\"16000\",\"fft_end_Q2\":\"16000\",\"fft_length_Lock\":\"8192\",\"fft_length_Q1\":\"16384\",\"fft_length_Q2\":\"16384\",\"fft_start_Lock\":\"4\",\"fft_start_Q1\":\"1\",\"fft_start_Q2\":\"1\",\"filter_Lock\":\"100\",\"filter_Q1\":\"1\",\"filter_Q2\":\"50\",\"fs_count_Lock\":\"8000\",\"fs_count_Q1\":\"16000\",\"fs_count_Q2\":\"16000\",\"fs_fre_Lock\":\"20000\",\"fs_fre_Q1\":\"10000\",\"fs_fre_Q2\":\"10000\"},\"shimmingParam\":{\"path0\":\"0\",\"path1\":\"0\",\"path2\":\"0.0213\",\"path3\":\"0.1016\",\"path4\":\"0.0102\",\"path5\":\"0.0474\",\"path6\":\"0.1397\",\"path7\":\"0.006\",\"path8\":\"-0.0495\",\"path9\":\"-0.0318\",\"path10\":\"-0.4729\",\"path11\":\"-0.1374\",\"path12\":\"0.0253\",\"path13\":\"0.1708\"}}"
    ```

- **"s_post_lock_data"** 
    说明：服务端主动发送锁场数据
    发送时机：随锁场周期定时发送
    报文体：
    ```json
     "{\"locking\":{\"frequency\":0.0,\"frequency0\":2.25035473405E7,\"frequency1\":9109648.4953,\"frequency2\":2.1170853918E7,\"hasPeak\":false,\"mt\":528.2940040425214,\"ppm\":3.7487,\"voltage\":0.0}}"
     ```

- **"s_post_sample_calibration_data"** 
    说明：服务端主动发送第三模块样品标定数据
    发送时机：登录成功后、标定过程、标定结束
    报文体1：
    ```json
    "{}" 
    ```
    报文体2：
    ```json
    "{\"calibrateResult\":{\"Q1_Mod1\":8889986.0,\"Q1_Mod2\":8889986.0,\"Q1_noise\":36593.61,\"Q2_Mod1\":291124.0,\"Q2_Mod2\":291124.0,\"Q2_noise\":1363.829,\"am90Q1\":39.7949,\"am90Q2\":47.0225,\"freF\":0.0,\"freH\":2.2527078929E7,\"freP\":9119174.2942,\"maxSigH\":2977.9178,\"maxSigP\":55.4591,\"sampleType\":0,\"widthH\":40.0,\"widthP\":40.0},\"sampleLock\":{\"frequency\":2.4414,\"frequency0\":2.2527078929E7,\"frequency1\":9119174.2942,\"frequency2\":2.11929919211E7,\"hasPeak\":true,\"mt\":528.8464321280632,\"ppm\":8.1763,\"voltage\":0.0}}"
    ```

- **"s_post_exp_queue_update"**
    说明：服务端主动发送更新实验队列(不包含实验参数等数据)
    发送时机：登录成功后、实验队列变动、实验状态变化
    报文体：
    ```json
    "{\"currentTaskId\":\"a000ba33-ac08-443e-a334-80548debed0d\",\"queue\":[{\"account\":\"\",\"createTime\":1748488326339,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"a000ba33-ac08-443e-a334-80548debed0d\",\"name\":\"Quantum Computing Task-326338\",\"params\":\"\",\"startTime\":1748488324348,\"state\":\"RUNNING\",\"type\":\"EXP_QALGORITHM\"}]}"
    ```
    queue：ExpTask[] ,ExpTask参考下面的说明
### 实验执行
- **"c_add_exp_task_req"** 
     说明：客户务端主动发送实验
    发送时机：客户端发送实验时
    报文体 ExpTask：
    ```json
    "{\"account\":\"Lab-746181000\",\"createTime\":1748488862602,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"3d4ccb10-d0fe-4c85-bb65-e4dc2e4eb4f7\",\"name\":\"Quantum Computing Task-862601\",\"params\":\"{\\\"circuit\\\":[],\\\"repeat\\\":0,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_QALGORITHM\"}"
    ```
    示例-核磁共振现象与信号：
    ```json
     "{\"account\":\"Lab-376503286\",\"createTime\":1748512965910,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"976dc507-286d-48f3-a807-6648bbe58419\",\"name\":\"\346\240\270\347\243\201\345\205\261\346\214\257\347\216\260\350\261\241\344\270\216\344\277\241\345\217\267-965909\",\"params\":\"{\\\"custom_freq\\\":true,\\\"freq_h\\\":0,\\\"freq_p\\\":0,\\\"repeat\\\":0,\\\"makePps\\\":false,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[]},\\\"samplePath\\\":0,\\\"sampleQubit\\\":0,\\\"usingAwgFile\\\":false}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_PULSE\"}"
     ```
    示例-拉比振荡：
    ```json
     "{\"account\":\"Lab-132740446\",\"createTime\":1748582123443,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"6ffaa548-c3f0-4b79-9d9c-5427784b8e80\",\"name\":\"\346\213\211\346\257\224\346\214\257\350\215\241-123442\",\"params\":\"{\\\"custom_freq\\\":false,\\\"freq_h\\\":22517957,\\\"freq_p\\\":9115482,\\\"repeat\\\":0,\\\"makePps\\\":true,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"samplePath\\\":0,\\\"sampleQubit\\\":0,\\\"usingAwgFile\\\":false}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_RABI\"}"
     ```
    示例-量子比特：
    ```json
     "{\"account\":\"Lab-132740446\",\"createTime\":1748582307285,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"8bd4227f-f94f-4d9e-8093-a92ed3f16f61\",\"name\":\"\351\207\217\345\255\220\346\257\224\347\211\271-307284\",\"params\":\"{\\\"custom_freq\\\":false,\\\"freq_h\\\":22517957,\\\"freq_p\\\":9115482,\\\"repeat\\\":0,\\\"makePps\\\":true,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"samplePath\\\":0,\\\"sampleQubit\\\":0,\\\"usingAwgFile\\\":false}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_QUBIT\"}"
     ```
    示例-量子退相干-T1：
    ```json
     "{\"account\":\"Lab-132740446\",\"createTime\":1748582389899,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"b9bb59fa-0ec7-418f-88d3-565f033910e0\",\"name\":\"\351\207\217\345\255\220\351\200\200\347\233\270\345\271\262-389898\",\"params\":\"{\\\"custom_freq\\\":false,\\\"freq_h\\\":22517957,\\\"freq_p\\\":9115482,\\\"repeat\\\":0,\\\"makePps\\\":true,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"samplePath\\\":0,\\\"sampleQubit\\\":0,\\\"usingAwgFile\\\":false}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_T1\"}"
     ```
    示例-量子退相干—T2：
    ```json
     "{\"account\":\"Lab-132740446\",\"createTime\":1748582389899,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"b9bb59fa-0ec7-418f-88d3-565f033910e0\",\"name\":\"\351\207\217\345\255\220\351\200\200\347\233\270\345\271\262-389898\",\"params\":\"{\\\"custom_freq\\\":false,\\\"freq_h\\\":22517957,\\\"freq_p\\\":9115482,\\\"repeat\\\":0,\\\"makePps\\\":true,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"samplePath\\\":0,\\\"sampleQubit\\\":0,\\\"usingAwgFile\\\":false}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_T2\"}"
    ```

    示例-量子控制：
    ```json
    "{\"account\":\"Lab-132740446\",\"createTime\":1748582683214,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"6de0f35a-5b95-4abd-967b-3fcc97f870df\",\"name\":\"\351\207\217\345\255\220\346\216\247\345\210\266-683213\",\"params\":\"{\\\"custom_freq\\\":false,\\\"freq_h\\\":22517957,\\\"freq_p\\\":9115482,\\\"repeat\\\":0,\\\"makePps\\\":false,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"samplePath\\\":0,\\\"sampleQubit\\\":0,\\\"usingAwgFile\\\":false}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_QCONTROL\"}"
    ```

    示例-量子初始化系统：
    ```json
    "{\"account\":\"Lab-132740446\",\"createTime\":1748582818193,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"7a9019ea-051b-45f8-9ece-98536638568a\",\"name\":\"\351\207\217\345\255\220\347\263\273\347\273\237\345\210\235\345\247\213\345\214\226-818192\",\"params\":\"{\\\"custom_freq\\\":false,\\\"freq_h\\\":22517957,\\\"freq_p\\\":9115482,\\\"repeat\\\":5,\\\"makePps\\\":false,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"samplePath\\\":-1,\\\"sampleQubit\\\":0,\\\"usingAwgFile\\\":false}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_PSTATE\"}"
    ```

    示例-量子逻辑门与量子线路-脉冲发送：
    ```json
    "{\"account\":\"Lab-132740446\",\"createTime\":1748583129324,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"aaabcf47-f3b1-4360-9c5a-7afbb551fe58\",\"name\":\"\351\207\217\345\255\220\351\200\273\350\276\221\351\227\250\344\270\216\351\207\217\345\255\220\347\272\277\350\267\257-129323\",\"params\":\"{\\\"custom_freq\\\":false,\\\"freq_h\\\":22517957,\\\"freq_p\\\":9115482,\\\"repeat\\\":0,\\\"makePps\\\":false,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"samplePath\\\":0,\\\"sampleQubit\\\":0,\\\"usingAwgFile\\\":false}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_QCIRCUIT_PULSE\"}"
    ```
    示例-量子逻辑门与量子线路-线路（<font color="purple">使用内置量子初始化参数</font>）：
    ```json
    "{\"account\":\"Lab-132740446\",\"createTime\":1748584001766,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"eb49b16b-94b0-40d4-8d15-8349a2a0dbe6\",\"name\":\"\351\207\217\345\255\220\346\200\201\351\207\215\346\236\204-001766\",\"params\":\"{\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":0,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"X0\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"X\\\"}],\\\"repeat\\\":0,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_QCIRCUIT_CIRCUIT\"}"
    ```
    示例-量子逻辑门与量子线路-线路（<font color="purple">使用自定义量子初始化参数</font>）：
    ```json
    "{\"account\":\"Lab-1268265271\",\"createTime\":1748586768009,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"{\\\"X0.spinq\\\":\\\"{\\\\\\\"description\\\\\\\":{\\\\\\\"DATE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"FIDELITY\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"OWNER\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"SLICES\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TITLE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TOTALPULSEWIDTH\\\\\\\":\\\\\\\"\\\\\\\"},\\\\\\\"pulse\\\\\\\":{\\\\\\\"channel1_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}],\\\\\\\"channel2_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}]}}\\\",\\\"customized_pps.spinq\\\":\\\"{\\\\\\\"description\\\\\\\":{\\\\\\\"DATE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"FIDELITY\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"OWNER\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"SLICES\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TITLE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TOTALPULSEWIDTH\\\\\\\":\\\\\\\"\\\\\\\"},\\\\\\\"pulse\\\\\\\":{\\\\\\\"channel1_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}],\\\\\\\"channel2_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}]}}\\\"}\",\"id\":\"c4273f0f-de35-43c9-9809-50038b5a1014\",\"name\":\"\351\207\217\345\255\220\346\200\201\351\207\215\346\236\204-768006\",\"params\":\"{\\\"Hlamda\\\":0.0,\\\"Plamda\\\":0.0,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":0,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"X0\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"X\\\"}],\\\"ppsFile\\\":\\\"customized_pps.spinq\\\",\\\"repeat\\\":1,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_QCIRCUIT_CIRCUIT\"}"
    ```
    示例-量子态重构（<font color="purple">使用自定义量子初始化参数</font>）：
    ```json
   "{\"account\":\"Lab-1493175700\",\"createTime\":1748588644465,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"{\\\"X0.spinq\\\":\\\"{\\\\\\\"description\\\\\\\":{\\\\\\\"DATE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"FIDELITY\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"OWNER\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"SLICES\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TITLE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TOTALPULSEWIDTH\\\\\\\":\\\\\\\"\\\\\\\"},\\\\\\\"pulse\\\\\\\":{\\\\\\\"channel1_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}],\\\\\\\"channel2_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}]}}\\\",\\\"customized_pps.spinq\\\":\\\"{\\\\\\\"description\\\\\\\":{\\\\\\\"DATE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"FIDELITY\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"OWNER\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"SLICES\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TITLE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TOTALPULSEWIDTH\\\\\\\":\\\\\\\"\\\\\\\"},\\\\\\\"pulse\\\\\\\":{\\\\\\\"channel1_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}],\\\\\\\"channel2_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}]}}\\\"}\",\"id\":\"bc06cec3-66e3-485e-ae12-c362a0bafa24\",\"name\":\"\351\207\217\345\255\220\346\200\201\351\207\215\346\236\204-644462\",\"params\":\"{\\\"Hlamda\\\":0.0,\\\"Plamda\\\":0.0,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":0,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"X0\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"X\\\"}],\\\"ppsFile\\\":\\\"customized_pps.spinq\\\",\\\"repeat\\\":1,\\\"samplePath\\\":0}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_QREFACTOR\"}"
    ```
    示例-量子计算任务（<font color="purple">使用自定义量子初始化参数</font>）：
    ```json
   "{\"account\":\"Lab-1493175700\",\"createTime\":1748588841513,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"{\\\"X0.spinq\\\":\\\"{\\\\\\\"description\\\\\\\":{\\\\\\\"DATE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"FIDELITY\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"OWNER\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"SLICES\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TITLE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TOTALPULSEWIDTH\\\\\\\":\\\\\\\"\\\\\\\"},\\\\\\\"pulse\\\\\\\":{\\\\\\\"channel1_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}],\\\\\\\"channel2_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}]}}\\\",\\\"customized_pps.spinq\\\":\\\"{\\\\\\\"description\\\\\\\":{\\\\\\\"DATE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"FIDELITY\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"OWNER\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"SLICES\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TITLE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TOTALPULSEWIDTH\\\\\\\":\\\\\\\"\\\\\\\"},\\\\\\\"pulse\\\\\\\":{\\\\\\\"channel1_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}],\\\\\\\"channel2_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}]}}\\\"}\",\"id\":\"249ed31e-08ad-470c-af2c-b92cd6c0e8b2\",\"name\":\"\351\207\217\345\255\220\350\256\241\347\256\227\344\273\273\345\212\241-841511\",\"params\":\"{\\\"Hlamda\\\":0.0,\\\"Plamda\\\":0.0,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":0,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"X0\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"X\\\"}],\\\"ppsFile\\\":\\\"customized_pps.spinq\\\",\\\"repeat\\\":1,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_QALGORITHM\"}"
    ```
    示例-初识算法实验：
    ```json
   "{\"account\":\"Lab-787377996\",\"createTime\":1748595025252,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"904b5b53-5ac8-4a9a-aa49-9f798a8d254a\",\"name\":\"\345\210\235\350\257\206\351\207\217\345\255\220\347\256\227\346\263\225-025251\",\"params\":\"{\\\"grover_bin\\\":0,\\\"calcMatrix\\\":true,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"}],\\\"repeat\\\":0,\\\"samplePath\\\":0}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_ALGORITHM_BASIC\"}"
    ```
    示例-Deutsch算法实验：
    ```json
   "{\"account\":\"Lab-787377996\",\"createTime\":1748595080762,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"2e9182f7-5069-423c-aaa6-536c1637359d\",\"name\":\"Deutsch\347\256\227\346\263\225-080760\",\"params\":\"{\\\"grover_bin\\\":0,\\\"calcMatrix\\\":true,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"I\\\"},{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":1,\\\"timeslot\\\":0,\\\"type\\\":\\\"X\\\"}],\\\"repeat\\\":0,\\\"samplePath\\\":0}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_DEUTSCH\"}"
    ```
    示例-Bernstein-Varirani算法实验：
    ```json
   "{\"account\":\"Lab-787377996\",\"createTime\":1748595160363,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"c2ca2dd6-81e4-43a4-b9e8-77794eace45b\",\"name\":\"Bernstein-Varirani\347\256\227\346\263\225-160363\",\"params\":\"{\\\"grover_bin\\\":0,\\\"calcMatrix\\\":true,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"},{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":1,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"}],\\\"repeat\\\":0,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_BERNSTEIN\"}"
    ```
    示例-Grover算法实验：
    ```json
   "{\"account\":\"Lab-787377996\",\"createTime\":1748595207819,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"19a94032-c65c-4812-8120-5a008691d763\",\"name\":\"Grover\347\256\227\346\263\225\345\256\236\351\252\214-207818\",\"params\":\"{\\\"grover_bin\\\":2,\\\"calcMatrix\\\":true,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"},{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":1,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"}],\\\"repeat\\\":0,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_GROVER\"}"
    ```
   示例-QFT算法实验：
    ```json
   "{\"account\":\"Lab-787377996\",\"createTime\":1748595207819,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"19a94032-c65c-4812-8120-5a008691d763\",\"name\":\"Grover\347\256\227\346\263\225\345\256\236\351\252\214-207818\",\"params\":\"{\\\"grover_bin\\\":2,\\\"calcMatrix\\\":true,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"},{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":1,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"}],\\\"repeat\\\":0,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_QFT\"}"
    ```
   示例-HHL算法实验：
    ```json
   "{\"account\":\"Lab-787377996\",\"createTime\":1748595207819,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"19a94032-c65c-4812-8120-5a008691d763\",\"name\":\"Grover\347\256\227\346\263\225\345\256\236\351\252\214-207818\",\"params\":\"{\\\"grover_bin\\\":2,\\\"calcMatrix\\\":true,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"},{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":1,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"}],\\\"repeat\\\":0,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_HHL\"}"
    ```
   示例-VQE算法实验：
    ```json
   "{\"account\":\"Lab-787377996\",\"createTime\":1748595207819,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"19a94032-c65c-4812-8120-5a008691d763\",\"name\":\"Grover\347\256\227\346\263\225\345\256\236\351\252\214-207818\",\"params\":\"{\\\"grover_bin\\\":2,\\\"calcMatrix\\\":true,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"},{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":1,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"}],\\\"repeat\\\":0,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_VQE\"}"
    ```
   示例-QAOA算法实验：
    ```json
   "{\"account\":\"Lab-787377996\",\"createTime\":1748595207819,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"19a94032-c65c-4812-8120-5a008691d763\",\"name\":\"Grover\347\256\227\346\263\225\345\256\236\351\252\214-207818\",\"params\":\"{\\\"grover_bin\\\":2,\\\"calcMatrix\\\":true,\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"},{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":1,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"}],\\\"repeat\\\":0,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_QAOA\"}"
    ```
   示例-自旋回波实验：
    ```json
   "{\"account\":\"Lab-787377996\",\"createTime\":1748596016019,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"1\",\"id\":\"164b45c7-ceae-449d-9aa0-5783b70d037b\",\"name\":\"\350\207\252\346\227\213\345\233\236\346\263\242-016018\",\"params\":\"{\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[]},\\\"samplePath\\\":0,\\\"sampleFre\\\":50000,\\\"sampleCount\\\":16000,\\\"sampleDelay\\\":0.0,\\\"h_freShift\\\":60,\\\"p_freShift\\\":0,\\\"h_freDemo\\\":30,\\\"p_freDemo\\\":0}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_SPINECHO\"}"
    ```
    示例-动力学解耦实验：
    ```json
    "{\"account\":\"Lab-126557732\",\"createTime\":1748921788671,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"0\",\"id\":\"549489e3-3c2d-400f-92b6-bc59c265eadd\",\"name\":\"\345\212\250\345\212\233\345\255\246\350\247\243\350\200\246-788670\",\"params\":\"{\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"samplePath\\\":1,\\\"sampleFre\\\":10000,\\\"sampleCount\\\":16000,\\\"sampleDelay\\\":0.0,\\\"h_freShift\\\":60,\\\"p_freShift\\\":80,\\\"h_freDemo\\\":30,\\\"p_freDemo\\\":30}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_DYDECO\"}"
    ```
    示例-形状脉冲实验：
    ```json
   "{\"account\":\"Lab-126557732\",\"createTime\":1748920900369,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"1\",\"id\":\"bb05a418-5b0d-4fc8-998a-e11da3320887\",\"name\":\"\345\275\242\347\212\266\350\204\211\345\206\262-900368\",\"params\":\"{\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[]},\\\"samplePath\\\":0,\\\"sampleFre\\\":10000,\\\"sampleCount\\\":16000,\\\"h_freShift\\\":60,\\\"p_freShift\\\":0,\\\"h_freDemo\\\":0,\\\"p_freDemo\\\":0}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_SHAPEPULSE\"}"
    ```
    示例-数值优化脉冲实验：
    ```json
   "{\"account\":\"Lab-126557732\",\"createTime\":1748922041870,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"0\",\"id\":\"6083995e-b1dd-422b-a5b9-2a539cfc3de1\",\"name\":\"\346\225\260\345\200\274\344\274\230\345\214\226\350\204\211\345\206\262-041869\",\"params\":\"{\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"samplePath\\\":-1,\\\"sampleFre\\\":10000,\\\"sampleCount\\\":16000,\\\"h_freShift\\\":58,\\\"p_freShift\\\":38,\\\"h_freDemo\\\":38,\\\"p_freDemo\\\":55}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_NPOPTI\"}"
    ```
    示例-物理层实验-自定义测量：
    ```json
   "{\"account\":\"Lab-126557732\",\"createTime\":1748922550704,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"146d29fc-4ac4-4162-ae97-d15a2efebe64\",\"name\":\"\347\211\251\347\220\206\345\261\202\345\256\236\351\252\214-550703\",\"params\":\"{\\\"h_freDemo\\\":0,\\\"h_freShift\\\":0,\\\"p_freDemo\\\":0,\\\"p_freShift\\\":0,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"gradient\\\":[{\\\"delay\\\":500,\\\"path\\\":1,\\\"value\\\":3.0}],\\\"compute_type\\\":0,\\\"relaxation_time\\\":\\\"15.0\\\",\\\"sampleCount\\\":16000,\\\"sampleDelay\\\":0,\\\"sampleFre\\\":50000,\\\"samplePath\\\":0,\\\"makePps\\\":true}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_LAYER_PHYSICAL\"}"
    ```
     示例-物理层实验-泡利分量测量：
    ```json
   "{\"account\":\"Lab-126557732\",\"createTime\":1748922621170,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"c304e137-fe51-4301-830d-ae3e4f9e3581\",\"name\":\"\347\211\251\347\220\206\345\261\202\345\256\236\351\252\214-621170\",\"params\":\"{\\\"h_freDemo\\\":0,\\\"h_freShift\\\":0,\\\"p_freDemo\\\":0,\\\"p_freShift\\\":0,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"gradient\\\":[{\\\"delay\\\":500,\\\"path\\\":1,\\\"value\\\":3.0}],\\\"compute_type\\\":1,\\\"relaxation_time\\\":\\\"15.0\\\",\\\"stepList\\\":[2,6],\\\"samplePath\\\":-1,\\\"makePps\\\":true}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_LAYER_PHYSICAL\"}"
    ```
    示例-物理层实验-量子态重构：
    ```json
   "{\"account\":\"Lab-126557732\",\"createTime\":1748922688256,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"24b104fe-400b-4ff9-bab0-b1d5cfcff4a5\",\"name\":\"\347\211\251\347\220\206\345\261\202\345\256\236\351\252\214-688255\",\"params\":\"{\\\"h_freDemo\\\":0,\\\"h_freShift\\\":0,\\\"p_freDemo\\\":0,\\\"p_freShift\\\":0,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"gradient\\\":[{\\\"delay\\\":500,\\\"path\\\":1,\\\"value\\\":3.0}],\\\"compute_type\\\":2,\\\"relaxation_time\\\":\\\"15.0\\\",\\\"samplePath\\\":-1,\\\"makePps\\\":true}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_LAYER_PHYSICAL\"}"
    ```
    示例-线路层实验-测试脉冲：
    ```json
   "{\"account\":\"Lab-126557732\",\"createTime\":1748931209335,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"id\":\"b3ce27e5-99e6-4204-ba28-156a9e0e149f\",\"name\":\"\347\272\277\350\267\257\345\261\202\345\256\236\351\252\214-209334\",\"params\":\"{\\\"custom_freq\\\":false,\\\"freq_h\\\":0,\\\"freq_p\\\":0,\\\"repeat\\\":0,\\\"makePps\\\":true,\\\"pulse\\\":{\\\"hPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}],\\\"pPulse\\\":[{\\\"am\\\":100.0,\\\"freshift\\\":0.0,\\\"phase\\\":0.0,\\\"width\\\":200.0}]},\\\"samplePath\\\":0,\\\"sampleQubit\\\":0,\\\"usingAwgFile\\\":false}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_LAYER_CIRCUIT_PULSE\"}"
    ```
    示例-线路层实验-线路实验：
    ```json
    "{\"account\":\"Lab-26935502\",\"createTime\":1748933813003,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"{\\\"Customizeder.spinq\\\":\\\"{\\\\\\\"description\\\\\\\":{\\\\\\\"DATE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"FIDELITY\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"OWNER\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"SLICES\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TITLE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TOTALPULSEWIDTH\\\\\\\":\\\\\\\"\\\\\\\"},\\\\\\\"pulse\\\\\\\":{\\\\\\\"channel1_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}],\\\\\\\"channel2_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}]}}\\\"}\",\"id\":\"273abdd7-9287-4100-a671-19eb5bee709b\",\"name\":\"\347\272\277\350\267\257\345\261\202\345\256\236\351\252\214-813000\",\"params\":\"{\\\"circuit\\\":[{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"Customizeder\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":0,\\\"timeslot\\\":0,\\\"type\\\":\\\"Customized\\\"},{\\\"angle\\\":0.0,\\\"belongQubit\\\":-1,\\\"controlQubit\\\":-1,\\\"controlQubit2\\\":-1,\\\"customtype\\\":\\\"\\\",\\\"delay\\\":0.0,\\\"qubitIndex\\\":1,\\\"timeslot\\\":0,\\\"type\\\":\\\"H\\\"}],\\\"relaxation_time\\\":\\\"15.0\\\",\\\"repeat\\\":0,\\\"samplePath\\\":-1}\",\"startTime\":0,\"state\":\"PENDING\",\"type\":\"EXP_LAYER_CIRCUIT_CIRCUIT\"}"
    ```

- **"s_add_exp_task_res"** 
    说明：服务端返回添加实验响应
    发送时机：服务端收到实验时
    报文体：
    ```json
    "{\"taskId\":\"8225428e-3b11-4d95-b049-2b54df82500f\",\"code\":0,\"message\":\"\"}"
    ```

- **"c_terminate_exp_task_req"**
    说明：客户端终止或移除实验
    发送时机：客户端主动发起删除或终止实验时
    报文体：
    ```json
     "{\"taskId\":\"8225428e-3b11-4d95-b049-2b54df82500f\"}"
     ```

- **"s_post_exp_removed"**
    说明：服务端主动通知“未在执行中的实验被移除”
    发送时机：实验队列中未在进行的实验被移除
    报文体：
    ```json
    "{\"taskId\":\"e0472bd2-4a81-434f-8f8d-0ec6d3b84742\"}"
    ```

- **"s_post_exp_started"** 
    说明：服务端主动通知“实验开始”，返回的是当前队列和当前实验id
    发送时机：实验开始执行
    报文体：
    ```json
    "{\"queue\":[{\"account\":\"\",\"createTime\":1748495618605,\"deviceId\":\"B16ECDD843BE4499\",\"endTime\":0,\"extra\":\"\",\"id\":\"59900df6-3799-468d-bf17-922fb43a1d61\",\"name\":\"\351\207\217\345\255\220\350\256\241\347\256\227\344\273\273\345\212\241-618604\",\"params\":\"\",\"startTime\":1748495619271,\"state\":\"RUNNING\",\"type\":\"EXP_QALGORITHM\"}],\"taskId\":\"59900df6-3799-468d-bf17-922fb43a1d61\"}"
    ```

- **"s_post_exp_step_changed"** 
    说明：服务端主发送实验步骤，返回当前实验步骤及当前实验id
    发送时机：实验过程中
    报文体：
    ```json
    "{\"data\":{\"description\":\"IDLE\",\"step\":\"IDLE\",\"time\":0},\"taskId\":\"59900df6-3799-468d-bf17-922fb43a1d61\"}"
    ```
    data：参考native sdk接口文档

- **"s_post_exp_data_updated"**
     说明：服务端主发送实验过程数据，返回当前实验过程数据及当前实验id
    发送时机：实验过程中（目前只有拉比振荡实验、和量子退相干实验会返回）
    报文体：
    ```json
    "{\"data\":{\"exp_rabi\":{\"amplitude\":-90.40712997647739,\"path\":0,\"width\":200}},\"taskId\":\"39437d2f-5b4f-4d15-a3d6-6fa7aa6c457a\"}"
    ```
    data：参考native sdk接口文档

- **"s_post_exp_chart_updated_started"**
     说明：服务端主发送实验开始接收chart数据的通知
    发送时机：实验过程中，当收到谱线数据时
    报文体：
    ```json
    "{\"group\":\"exp_rabi\",\"path\":\"0\",\"taskId\":\"39437d2f-5b4f-4d15-a3d6-6fa7aa6c457a\"}"
    ```

- **"s_post_exp_chart_updated"**
     说明：服务端主发送实验步骤，返回当前实验步骤及当前实验id
    发送时机：实验过程中
    报文体：ChartData

- **"s_post_exp_chart_updated_finished"**
     说明：服务端主发送实验结束接收chart数据的通知
    发送时机：实验过程中
    报文体：
    ```json
    "{\"group\":\"exp_rabi\",\"path\":\"0\",\"taskId\":\"635be9fd-1329-4ee5-aaa5-b46abc3c71f6\"}"
    ```
- **"s_post_exp_finished"**
     说明：服务端主发送实验结束
    发送时机：实验结束
    报文体：
    ```json
    "{\"data\":{\"isTerminated\":false,\"operation\":\"exp_qubit\",\"parameters\":{\"path\":0,\"result\":\"{\\\"coordinate\\\":{\\\"phi\\\":0,\\\"theta\\\":0,\\\"x\\\":0,\\\"y\\\":0,\\\"z\\\":0},\\\"imag\\\":[0,0,0,0],\\\"module\\\":[0.5,0.5],\\\"real\\\":[0.5,0,0,0.5]}\"}},\"taskId\":\"37015dab-d64e-42a3-970a-4b20fe384d5f\"}"
    ```
    data：参考native sdk接口文档

## 数据类型
### ExpTask
说明：实验任务类，队列更新、发送实验
| 字段       | 类型       | 说明 |
|-----------|------------ |------|
| **type**  | OperatorType |    实验类型,见下面的OperatorType    |
| **id**  | String |    实验ID    |
| **state**  | TaskState |    状态见下面的TaskState，发送过来的实验应为：TaskState.PENDING   |
| **account**  | String |    用户登录时的名称    |
| **deviceId**  | String |    发送实验过来的设备id    |
| **name**  | String |    实验名称    |
| **params**  | String |    实验参数,见native sdk接口文档    |
| **extra**  | String |    额外参数，如第三模块，传入样品类型"0":亚磷酸二甲酯; "1":水    |
| **createTime**  | Long |    创建时间    |
| **startTime**  | Long |    开始时间    |
| **endTime**  | Long |    结束时间    |

### ExpTask.extra
##### 自定义门作为extra
    extra为[key]:[value]键值对的json，key为自定义量子门的名称，value为自定义量子门的脉冲文件内容
- 量子逻辑门与量子线路：
- 量子态重构：
- 量子计算任务：
- 线路层实验：
```json
"{\\\"Customizeder.spinq\\\":\\\"{\\\\\\\"description\\\\\\\":{\\\\\\\"DATE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"FIDELITY\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"OWNER\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"SLICES\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TITLE\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"TOTALPULSEWIDTH\\\\\\\":\\\\\\\"\\\\\\\"},\\\\\\\"pulse\\\\\\\":{\\\\\\\"channel1_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}],\\\\\\\"channel2_pulse\\\\\\\":[{\\\\\\\"amplitude\\\\\\\":100.0,\\\\\\\"detuning\\\\\\\":0.0,\\\\\\\"phase\\\\\\\":0.0,\\\\\\\"width\\\\\\\":200.0}]}}\\\"}"
```
##### 样本类型作为extra
    extra ："0"为亚磷酸二甲酯，"1"为水
- 自旋回波
- 动力学解耦
- 形状脉冲
- 数值优化脉冲

### OperatorType
    IDLE:空闲 （不支持发送实验）
    CALIBRATION：仪器校准（不支持发送实验）
    PULSE:仪器调试-发送核磁脉冲（不支持发送实验）
    RABI：仪器调试-拉比振荡（不支持发送实验）
    SHIMMING：仪器调试-自动匀场（不支持发送实验）
    FREQUENCY：仪器调试-频率校准（不支持发送实验）
    PHASE：仪器调试-相位校准（不支持发送实验）
    POWER：仪器调试-90度校准（不支持发送实验）
    PPS：仪器调试-PPS校准（不支持发送实验）
    T1：仪器调试-T1校准（不支持发送实验）
    T2：仪器调试-T2校准（不支持发送实验）
    AUTO_SHIMMING：仪器调试-自动快速匀场
    EXP_PULSE：核磁共振现象与信号实验
    EXP_RABI：拉比振荡实验
    EXP_QUBIT: 量子比特实验
    EXP_T1：量子退相干-T1实验
    EXP_T2：量子退相干-T2实验 
    EXP_QCONTROL：量子控制实验
    EXP_PSTATE：量子系统初始化实验
    EXP_QCIRCUIT_PULSE：量子线路实验-发送脉冲
    EXP_QCIRCUIT_CIRCUIT：量子线路实验-线路实验 
    EXP_QREFACTOR：量子态重构实验
    EXP_QALGORITHM：量子计算任务实验
    EXP_ALGORITHM_BASIC：初始算法实验
    EXP_DEUTSCH：Deutsch算法实验
    EXP_BERNSTEIN：Bernstein-Varirani算法实验
    EXP_GROVER：Grover算法实验
    EXP_VQE：VQE算法实验
    EXP_QAOA：QAOA算法实验
    EXP_QFT：QFT算法实验
    EXP_HHL：HHL算法实验
    EXP_SPINECHO：自旋回波实验
    EXP_DYDECO：动力学解耦实验
    EXP_SHAPEPULSE：形状脉冲实验
    EXP_NPOPTI：数值优化脉冲实验
    EXP_SAMPLE_CALIBRATION：样品标定（不支持发送实验）
    EXP_LAYER_PHYSICAL：物理层实验
    EXP_LAYER_CIRCUIT_CIRCUIT：线路层实验-线路实验
    EXP_LAYER_CIRCUIT_PULSE：线路层实验-发送脉冲
    EXP_MIXING_CIRCUIT：经典混合实验（不支持发送实验）

### TaskState：
    PENDING：等待中
    RUNNING： 执行中
    COMPLETED： 正常完成

    