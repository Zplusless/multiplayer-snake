# snake client used in container live migration
# Because 
# https://github.com/Zplusless/ServiceMigration





import asyncio
import websockets
import json
import argparse



done = False



# log
import time
import logging
import socket
hostname = socket.gethostname()
current_milli_time = lambda: time.time() * 1000  #lambda: int(round(time.time() * 1000))
logging.basicConfig(
    level=logging.INFO, 
    format= f'%(asctime)s - {hostname} - %(levelname)s - %(message)s', #'%(asctime)s - %(levelname)s - %(message)s',
    filename='node_log/srvMig.log',
    filemode='a',##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
    )
log = logging.getLogger('snake_log')



# 引入画图
from curses_graphic import Graphic


# # curses
# import curses

# # 初始化屏幕
# stdscr = curses.initscr()

# # 不回显按键
# curses.noecho()

# # 立即响应按键，而不需要按下回车键
# curses.cbreak()

# # 非阻塞模式
# # stdscr.nodelay(True)

# # 让预置的KEY_*变量生效
# stdscr.keypad(True)

# # 允许使用颜色
# curses.start_color()
# # 0:black, 1:red, 2:green, 3:yellow, 4:blue, 5:magenta, 6:cyan 和 7:white
# curses.init_pair(1, curses.COLOR_RED, curses.COLOR_RED)
# curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_GREEN)
# curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
# curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLUE)
# curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
# curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_CYAN)
# curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_WHITE)


# def pixel(line, colomn, symbol, color):
#     """
#     将输入的符号，转化成对应的颜色块
#     #! 注意，curses里的坐标是(y,x)，与常规坐标是反的

#     输入的symbol：
#     ' '---> 空白场地
#     '%'---> 蛇头
#     '@'---> 蛇身子
#     '*'---> 蛇尾巴
#     '0~9'---> 食物
#     '#'---> 石头
#     其它--->墙
#     """
#     out_symbol = '  '
#     out_color =  curses.color_pair(color)
#     if symbol == '#':
#         out_color = curses.color_pair(7)
#     elif symbol.isdigit():
#         out_symbol = ' '+symbol
#         out_color = curses.color_pair(0)
        
#     return line, 2*colomn-1, out_symbol, out_color





class SnakeClient(object):

    def __init__(self, player_name="snake", host='127.0.0.1', port="5500"):
        super().__init__()
        # screen.fill((30, 30, 30))
        # self.btnJoin = Button(10, 10, 50, 32, "join", "join", False)
        # self.btnDisConnect = Button(100, 10, 50, 32, "quit", "quit", False)
        # self.model = StandardItemModel(10, 52, 25, 50)

        self.graph = Graphic()
        self.window_lines=None # 游戏区场地有多少行
        self.window_columns=None # 游戏区场地有多少列

        self.can_join=False

        self.playerName = player_name
        self.playerId = 0
        self.HOST = host
        self.PORT = port
        # self.color = [(255, 255, 255), (255, 0, 0), (255, 255, 0),
                    #   (0, 255, 0), (0, 255, 255), (0, 0, 255), (255, 0, 255)]
        
        self.record_time = False
        self.t1 = None
        self.t2 = None

    async def send_msg(self, websocket, msgList):
        msg = json.dumps(msgList)
        if msg == "exit":
            print(f'you have enter "exit", goodbye')
            await websocket.close(reason="user exit")
            return False
        await websocket.send(msg)

    async def recv_msg(self, websocket):
        global done
        while not done:
            await asyncio.sleep(0.1)
            try:
                message = await websocket.recv()
                # print(message)
                gs = json.loads(message)
                if not isinstance(gs[0], list):
                    gs = [gs]
                for i in range(len(gs)):
                    args = gs[i]
                    cmd = gs[i][0]

                    print(f'new message ---> {cmd}')

                    if cmd == "handshake":
                        self.playerId = args[2]
                    elif cmd == "world":
                        self.initWorld(args[1])
                    elif cmd == "reset_world":
                        self.can_join=True  # 如果是False，当多个用户接入但是没有开始，则前面接入的会无法join
                        self.resetWorld()
                    elif cmd == "p_joined":
                        id = args[1]
                        if id == self.playerId:
                            # self.btnJoin.setEnabled(False)
                            self.can_join=False
                    elif cmd == "render":
                        x = int(args[1])
                        y = int(args[2])
                        temp = str(args[3])
                        color = int(args[4])

                        self.graph.draw_pixel(x,y,temp,color)
                        print(f"render a '{temp}' ")
                        # if temp in " %@*0123456789":
                        #     self.graph.draw_pixel(x,y,temp,color)
                        #     print(f"render a '{temp}' ")



                        # item = StandardItem()
                        # # Item.setTextAlignment(Qt.AlignCenter | Qt.AlignHCenter | Qt.AlignHCenter)
                        # if temp == " ":
                        #     item.setBackground(pg.Color(0, 0, 0))
                        # elif temp == "%":
                        #     item.setBackground(pg.Color(130, 130, 130))
                        # elif temp == "@" or temp == "*" or '0' <= temp <= '9' or temp == '#':
                        #     item.setBackground(pg.Color(self.color[color][0], self.color[color][1], self.color[color][2]))
                        # else:
                        #     item.edge = 1
                        #     item.setText(temp)
                        #     item.setBackground(pg.Color(82, 139, 139))
                        #     item.setForeground(pg.Color(self.color[color][0], self.color[color][1], self.color[color][2]))
                        # # Item.setFont(QFont("Helvetica"))
                        # self.model.setItem(y, x, item)
                    elif cmd == "p_enable_join":
                        id = args[1]
                        if id == self.playerId:
                            # self.btnJoin.setEnabled(True)
                            self.can_join=True
                    elif cmd == "p_join_switch_confirm":
                        id = args[1]
                        if id == self.playerId:
                            print(f'\n\n\n\nreceived p_joined---> record_time_flag={self.record_time}')
                            if self.record_time:
                                self.t2 = current_milli_time()
                                log.info(self.t2-self.t1)
                                self.record_time = False
                                print(f'logging at {self.t2}, record_time_flag--->{self.record_time}\n\n\n\n\n')
                    elif cmd == "p_gameover":
                        id = args[1]
                        # remove
                        if id == self.playerId:
                            # self.btnJoin.setEnabled(True)
                            self.can_join=True
                            print(f'player main ws exit,good bye')
                            await websocket.close(reason="user exit")
                            done = True
                            return False
            except websockets.exceptions.ConnectionClosedOK:
                done = True
                return

    async def client(self, websocket):
        # 客户端界面，绘制界面，发送指令
        global done
        while not done:
            await asyncio.sleep(0.1)

            key = self.graph.stdscr.getch()

            if key ==27:
                done = True
                await websocket.close()
                return
            elif key == ord('j') and self.can_join:
                self.t1 = current_milli_time()
                self.record_time = True

                print(f'\n\n\n\nclick join button at {self.t1}, record_time_flag--->{self.record_time} \n\n\n\n')

                await self.send_msg(websocket, ["join"])
                self.can_join=False

            elif key == ord('q'):
                done = True
                await  websocket.close(reason="user exit")
                return
            elif key in [self.graph.K_UP, self.graph.K_LEFT, self.graph.K_RIGHT, self.graph.K_DOWN]:
                code = "0"
                if key == self.graph.K_LEFT:
                    code = "37"
                elif key == self.graph.K_UP:
                    code = "38"
                elif key == self.graph.K_RIGHT:
                    code = "39"
                elif key == self.graph.K_DOWN:
                    code = "40"
                print(code)
                if code == "37" or code == "38" or code == "39" or code == "40":
                    await websocket.send(code)
                else:
                    pass

            self.graph.refresh()
            await asyncio.sleep(1/self.graph.fps)

            # screen.fill((30, 30, 30))   # 设定背景颜色
            # self.btnJoin.draw(screen)
            # self.btnDisConnect.draw(screen)
            # self.model.draw(screen)
            # pg.display.flip()  # 刷新屏幕
            # clock.tick(30)

    async def game(self):
        async with websockets.connect("ws://" + self.HOST + ":" + self.PORT + "/connect") as websocket:
            await self.send_msg(websocket, ["new_player", self.playerName])
            # 连接成功发送用户信息登录

            # self.btnJoin.setEnabled(True)
            self.can_join=True
            # self.btnDisConnect.setEnabled(True)
            # 参加游戏按钮和断开连接按钮可以点击

            client = asyncio.get_event_loop().create_task(self.client(websocket))
            # 客户端界面协程
            rec = asyncio.get_event_loop().create_task(self.recv_msg(websocket))
            # 消息协程
            await client
            await rec
            # 客户端界面与消息并发

    def initWorld(self, data):

        self.window_lines=len(data) # 游戏区场地有多少行
        self.window_columns=len(data[0]) # 游戏区场地有多少列
        self.graph.draw_window(self.window_lines,self.window_columns)

        for y in range(len(data)):
            for x in range(len(data[y])):
                temp = str(data[y][x][0])
                color = int(data[y][x][1])

                # draw_pixel是在墙内的区域，以0，0为起点，画图
                self.graph.draw_pixel(y,x, temp, color)

                # item = StandardItem()
                # if temp == " ":
                #     item.setBackground(pg.Color(0, 0, 0))
                # elif temp == "%":
                #     item.setBackground(pg.Color(130, 130, 130))
                # elif temp == "@" or temp == "*" or '0' <= temp <= '9' or temp == '#':
                #     item.setBackground(pg.Color(self.color[color][0], self.color[color][1], self.color[color][2]))
                # else:
                #     item.edge = 1
                #     item.setText(temp)
                #     # print(temp)
                #     item.setBackground(pg.Color(82, 139, 139))
                #     item.setForeground(pg.Color(self.color[color][0], self.color[color][1], self.color[color][2]))
                #     # Item.setFont(QFont("Helvetica"))
                # self.model.setItem(y, x, item)

    def resetWorld(self):
        for y in range(self.window_lines):  # 25
            for x in range(self.window_columns): # 50
                self.graph.draw_pixel(y,x,' ', 0)
                # Item = StandardItem()
                # Item.setBackground(pg.Color(0, 0, 0))
                # self.model.setItem(y, x, Item)
    
    # def quit(self):
    #     pg.quit()


if __name__ == '__main__':

    log.warning('\n\n========new experiment==========\n\n')

    parser = argparse.ArgumentParser(description='user name, ip, port')
    
    parser.add_argument('-n', '--name', type=str, help='user name')
    parser.add_argument('-i', '--ip', type=str, help='ip')
    parser.add_argument('-p', '--port', type=str, help='name')

    args = parser.parse_args()

    name = args.name
    ip = args.ip
    port = args.port

    if not(name and ip and port):
        raise Exception('name, ip, port are needed')
    temp = SnakeClient(name, ip, port)
    asyncio.get_event_loop().run_until_complete(temp.game())
    print("end")