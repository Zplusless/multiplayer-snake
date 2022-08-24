# 通信协议

client和server通过websocket通信，每次发送的内容为一个list，其中list[0]为操作的名称，如“render”，list后续的数据为具体参数，如snake的坐标

## client--->server

按照启动后发送的顺序

