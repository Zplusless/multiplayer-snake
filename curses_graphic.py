import curses



class Graphic:
    def __init__(self) -> None:
        # snake每秒钟前进几步
        self.fps = 2
         
        # 初始化屏幕
        self.stdscr = curses.initscr()
        # 此处不应该阻塞
        self.stdscr.nodelay(True)
        # 不回显按键
        curses.noecho()
        # 立即响应按键，而不需要按下回车键
        curses.cbreak()
        # 让预置的KEY_*变量生效
        self.stdscr.keypad(True)



        # 上下左右建
        self.K_UP = curses.KEY_UP
        self.K_LEFT = curses.KEY_LEFT
        self.K_RIGHT = curses.KEY_RIGHT
        self.K_DOWN = curses.KEY_DOWN

       
        # 允许使用颜色
        curses.start_color()
        # 0:black, 1:red, 2:green, 3:yellow, 4:blue, 5:magenta, 6:cyan 和 7:white
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLUE)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_CYAN)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_WHITE)

        self.window = None
        self.window_loc = 2, 0
        # 输入说明
        self.stdscr.addstr(0,0,"press j to join, press q to disconnect")
        self.stdscr.addstr(1,0,"press esc to quit")

    def draw_window(self, height, width):
        # i = 1
        self.window = self.stdscr.subwin(height+2, 2*width+2,  # 大小
                                    self.window_loc[0], self.window_loc[1])     # 位置
        # subwin.nodelay(True)
        self.window.keypad(True)

        # 边界是占用实际行数的，故如果画边界，则第0行/列，最后一行/列将被占用，所以subwin大小要比需求+2
        self.window.border() 


    def pixel(self, line, colomn, symbol, color):
        """
        将输入的符号，转化成对应的颜色块
        #! 注意，curses里的坐标是(y,x)，与常规坐标是反的

        输入的symbol：
        ' '---> 空白场地
        '%'---> 蛇头
        '@'---> 蛇身子
        '*'---> 蛇尾巴
        '0~9'---> 食物
        '#'---> 石头
        其它--->墙
        """
        # line和colomn为0时对应的都是边界墙，所以要加1
        line+=1
        colomn+=1

        out_symbol = '  '
        out_color =  curses.color_pair(color)
        if symbol == '#':
            out_color = curses.color_pair(7)
        elif symbol.isdigit():
            out_symbol = ' '+symbol
            out_color = curses.color_pair(0)
            
        return line, 2*colomn-1, out_symbol, out_color
    
    def draw_pixel(self, line: int, column: int, symbol: str, color: int):
        if color< 0 or color >7:
            raise Exception('wrong color id')

        self.window.addstr(*self.pixel(line, column, symbol, color))
    
    # 刷新屏幕内容
    def refresh(self):
        self.stdscr.refresh()
        if self.window:
            self.window.refresh()

        # print('game window refresh ---> done')
    

