from random import randint, choice
import json

import settings
from player import Player
from datatypes import Char, Draw


class Game:

    def __init__(self):
        self._last_id = 0
        self._colors = []
        self._players = {}
        self._top_scores = []
        self._world = []
        self.running = False
        self.create_world()
        self.read_top_scores()

    def create_world(self):
        for y in range(0, settings.FIELD_SIZE_Y):
            self._world.append([Char(" ", 0)] * settings.FIELD_SIZE_X)

    def reset_world(self):
        for y in range(0, settings.FIELD_SIZE_Y):
            for x in range(0, settings.FIELD_SIZE_X):
                if self._world[y][x].char != " ":
                    self._world[y][x] = Char(" ", 0)
        self.send_all("reset_world")

    def new_player(self, name, ws):
        self._last_id += 1
        player_id = self._last_id
        if( name != "visitor"):
            self.send_personal(ws, "handshake", name, player_id)
            self.send_personal(ws, "world", self._world)

        self.send_personal(ws, *self.top_scores_msg())
        for p in self._players.values():  # 把已有player的信息发给新用户
            if p.alive:
                self.send_personal(ws, "p_joined", p._id, p.name, p.color, p.score)

        player = Player(player_id, name, ws)
        self._players[name] = player
        return player

    # 将新的接入的ws记录在内
    def add_player_ws(self, player: Player, ws):
        player.ws.append(ws)
        self.send_personal(ws, "handshake", player.name, player._id)
        self.send_personal(ws, "world", self._world)
        print(f'player-{player._id} ws list: {player.ws}')

    def get_player_by_name(self, name):
        if name in self._players.keys():
            return self._players[name]
        else:
            return None

    def join(self, player):
        if player.name != "visitor":
            if player.alive:
                return
            if self.count_alive_players() == settings.MAX_PLAYERS:
                self.send_personal(player.ws, "error", "Maximum players reached")
                return
            # pick a color
            if not len(self._colors):
                # color 0 is reserved for interface and stones
                self._colors = list(range(1, settings.NUM_COLORS + 1))
            color = choice(self._colors)
            self._colors.remove(color)
            # init snake
            player.new_snake(color)
            # notify all about new player
            self.send_all("p_joined", player._id, player.name, color, 0)

    def enable_join_non_main_ws(self, player: Player):
        self.send_personal(player.main_ws, "p_join_switch_confirm", player._id)

        for ws in player.ws:
            if ws!=player.main_ws:
                self.send_personal(ws, "p_enable_join", player._id)


    def game_over(self, player):
        player.alive = False
        self.send_all("p_gameover", player._id)
        self._colors.append(player.color)
        self.calc_top_scores(player)
        self.send_all(*self.top_scores_msg())

        render = player.render_game_over()
        if not self.count_alive_players():
            render += self.render_text(" >>> GAME OVER <<< ",
                                       randint(1, settings.NUM_COLORS))
            self.store_top_scores()
        return render


    def calc_top_scores(self, player):
        if not player.score:
            return
        ts_dict = dict(self._top_scores)
        if player.score <= ts_dict.get(player.name, 0):
            return
        ts_dict[player.name] = player.score
        self._top_scores = sorted(ts_dict.items(), key=lambda x: -x[1])
        self._top_scores = self._top_scores[:settings.MAX_TOP_SCORES]

    def top_scores_msg(self):
        top_scores = [(t[0], t[1], randint(1, settings.NUM_COLORS))
                       for t in self._top_scores]
        return ("top_scores", top_scores)

    def read_top_scores(self):
        try:
            f = open("top_scores.txt", "r+")
            content = f.read()
            if content:
                self._top_scores = json.loads(content)
            else:
                self._top_scores = []
            f.close()
        except FileNotFoundError:
            pass

    def store_top_scores(self):
        f = open("top_scores.txt", "w")
        f.write(json.dumps(self._top_scores))
        f.close()


    def player_disconnected(self, player: Player, ws):
        
        if ws == player.main_ws:
            # for ws in player.ws:
            #     self.send_personal(ws, "p_gameover", player._id)
            ## player.ws.clear()  # 主ws断开，则结束
            player.ws.remove(ws)
            if player.alive:
                render = self.game_over(player)
                self.apply_render(render)

            del self._players[player.name]
            del player
        else:
            if ws in player.ws:
                player.ws.remove(ws)  # 副ws断开，则仅仅去除这个ws



    def count_alive_players(self):
        return sum([int(p.alive) for p in self._players.values()])

    def next_frame(self):
        messages = []
        render_all = []
        for p_name, p in self._players.items():

            if not p.alive:
                continue
            # check if snake already exists
            if len(p.snake):
                # check next position's content
                pos = p.next_position()
                # check bounds
                if pos.x < 0 or pos.x >= settings.FIELD_SIZE_X or\
                   pos.y < 0 or pos.y >= settings.FIELD_SIZE_Y:

                    # render_all += self.game_over(p)

                    #* 蛇碰到边界就重新初始化
                    render_all += p.render_new_snake()
                    continue

                char = self._world[pos.y][pos.x].char
                grow = 0
                if char.isdigit():
                    # start growing next turn in case we eaten a digit
                    grow = int(char)
                    p.score += grow
                    messages.append(["p_score", p_name, p.score])
                elif char != " ":
                    render_all += self.game_over(p)
                    continue

                render_all += p.render_move()
                p.grow += grow

                # spawn digits proportionally to the number of snakes
                render_all += self.spawn_digit()
            else:
                # newborn snake
                render_all += p.render_new_snake()
                # and it's birthday present
                render_all += self.spawn_digit(right_now=True)

        # # 生成石头
        # render_all += self.spawn_stone()

        # send all render messages
        self.apply_render(render_all)
        # send additional messages
        if messages:
            self.send_all_multi(messages)

    def _get_spawn_place(self):
        x = None
        y = None
        for i in range(0,2):
            x = randint(0, settings.FIELD_SIZE_X - 1)
            y = randint(0, settings.FIELD_SIZE_Y - 1)
            if self._world[y][x].char == " ":
                break
        return x, y

    def spawn_digit(self, right_now=False):
        render = []
        if right_now or\
           randint(1, 100) <= settings.DIGIT_SPAWN_RATE:
            x, y = self._get_spawn_place()
            if x and y:
                char = str(randint(1,9))
                color = randint(1, settings.NUM_COLORS)
                render += [Draw(x, y, char, color)]
        return render

    def spawn_stone(self, right_now=False):
        render = []
        if right_now or\
           randint(1, 100) <= settings.STONE_SPAWN_RATE:
            x, y = self._get_spawn_place()
            if x and y:
                render += [Draw(x, y, '#', 0)]
        return render

    def apply_render(self, render):
        messages = []
        for draw in render:
            # apply to local
            self._world[draw.y][draw.x] = Char(draw.char, draw.color)
            # send messages
            messages.append(["render"] + list(draw))
        self.send_all_multi(messages)

    def render_text(self, text, color):
        # render in the center of play field
        posy = int(settings.FIELD_SIZE_Y / 2)
        posx = int(settings.FIELD_SIZE_X / 2 - len(text)/2)
        render = []
        for i in range(0, len(text)):
            render.append(Draw(posx + i, posy, text[i], color))
        return render

    def send_personal(self, ws, *args):
        if not isinstance(ws, list):
            ws = [ws]
        
        msg = json.dumps([args])
        for s in ws:
            s.send_str(msg)

    def send_all(self, *args):
        self.send_all_multi([args])

    def send_all_multi(self, commands):
        msg = json.dumps(commands)
        for player in self._players.values():
            for ws in player.ws:
                if ws:
                    ws.send_str(msg)

