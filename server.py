import os
import asyncio
import json
from player import Player
from aiohttp import web

import settings
from game import Game

# async def handle(request):
#     ALLOWED_FILES = ["index.html", "style.css",'jquery-2.2.1.min.js']
#     name = request.match_info.get('name', 'index.html')
#     if name in ALLOWED_FILES:
#         try:
#             with open(name, 'rb') as index:
#                 return web.Response(body=index.read(), content_type='text/html')
#         except FileNotFoundError:
#             pass
#     return web.Response(status=404)


async def wshandler(request):
    print("Connected")
    app = request.app
    game:Game = app["game"]
    ws = web.WebSocketResponse()
    print(f'ws: {id(ws)}')
    await ws.prepare(request)

    # todo 
    #* 在此处做一个检查，如果name已经有了，就让player指向已经有的，并且替换对应的websocket

    player = None
    while True:
        msg = await ws.receive()
        if msg.tp == web.MsgType.text:
            print("Got message %s" % msg.data)

            data = json.loads(msg.data)
            if type(data) == int and player:
                # 只有主ws有效
                if ws == player.main_ws:
                    # Interpret as key code
                    player.keypress(data)
            if type(data) != list:
                continue
            if not player:
                if data[0] == "new_player":
                    name = data[1]
                    player:Player = game.get_player_by_name(name)
                    if player:
                        game.add_player_ws(player, ws)
                    else:
                        player = game.new_player(name, ws)
                        
            elif data[0] == "join":
                if not game.running:  # 只有第一个用户join才会触发reset_world
                    game.reset_world()

                    print("Starting game loop")
                    asyncio.ensure_future(game_loop(game))
                
                # 首次join的player没有main_ws,有main_ws的必为已经join过的
                if not player.main_ws: # 仅第一次加入会触发
                    game.join(player)

                # 设定主ws，只有主ws的方向操作才有效
                player.main_ws = ws

                # 释放非main_ws对应client的join按键
                game.enable_join_non_main_ws(player)

                

        elif msg.tp == web.MsgType.close:
            break

    if player:
        game.player_disconnected(player, ws)

    print("Closed connection")
    return ws

async def game_loop(game):
    game.running = True
    while 1:
        game.next_frame()
        if not game.count_alive_players():
            print("Stopping game loop")
            break
        await asyncio.sleep(1./settings.GAME_SPEED)
    game.running = False


event_loop = asyncio.get_event_loop()
event_loop.set_debug(True)

app = web.Application()

app["game"] = Game()


app.router.add_route('GET', '/connect', wshandler)
# app.router.add_route('GET', '/{name}', handle)
# app.router.add_route('GET', '/', handle)

# get port for heroku
port = int(os.environ.get('PORT', 5500))
web.run_app(app, port=port)
