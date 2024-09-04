#code
import threading
import statsapi
import time
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from network import tcp_server, udp_server, tcp_client, udp_client

def main():
    global signal
    global gamestarted 
    signal = {}
    signal['shutdown'] = False
    #INITILIZE THREADS - tcp_server AND udp_server FROM THE network.py FILE
    global tcp_thread
    tcp_thread = threading.Thread(target=tcp_server, args=('localhost', 4390, signal, lambda message: respond(message),), name="tcp_server")
    tcp_thread.daemon = True  # Set as daemon so the thread will exit when the main program exits
    tcp_thread.start()
    host = 1

    slate()

    # Get the current season
    # Get the current date
def slate():
    current_date = datetime.now().replace(microsecond=0)
    current_date += timedelta(hours=16, minutes=50)
    todays_date = current_date
    while True:
        if current_date.hour < 3:
            current_date -= timedelta(hours=3)

    # Format the date as MM/DD/YYYY
        formatted_date = current_date.strftime('%m/%d/%Y')# Format the date as MM/DD/YYYY

        current_sched = statsapi.schedule(start_date=formatted_date,end_date=formatted_date)
        game_info = {}
        counter = 1
        for game in current_sched:
            parsed_datetime = datetime.strptime(game['game_datetime'], '%Y-%m-%dT%H:%M:%SZ')
            adjusted_datetime = parsed_datetime - timedelta(hours=4)
            
            game_time_str = adjusted_datetime.strftime('%I:%M %p')
            game_time = datetime.strptime(game_time_str, '%I:%M %p')
            game_info[counter] = {}
            game_info[counter]['game_id'] = game['game_id']
            game_info[counter]['away_id'] = game['away_id']
            game_info[counter]['home_id'] = game['home_id']
            game_info[counter]['home_pitcher'] = game['home_probable_pitcher']
            game_info[counter]['away_pitcher'] = game['away_probable_pitcher']
            game_info[counter]['time'] = game_time_str
            game_info[counter]['status'] = game['status']
            

            print(f"{str(counter).rjust(2)}) {game['away_name'] + ' @ ' + game['home_name']}".ljust(50) + f" {game_time_str} ------ {game['status']}")
            counter+=1
        game_focus = -1
        print("\n")
        game_focus = input("What game would you like to follow? Type 'back' to go to yesterday, 'next' to go to tomorrow, or 'exit' to quit: ").strip().lower()

        if game_focus == 'exit':
            signal['shutdown'] = True
            message_dict = json.dumps({
                "message_type": "shutdown",
            })
            try:
                tcp_client('localhost', 4391, message_dict)
            except:
                pass
            tcp_thread.join()
            exit()

        if game_focus == 'back':
            current_date -= timedelta(days=1)
            continue

        if game_focus == 'next':
            current_date += timedelta(days=1)
            continue

        try:
            game_focus = int(game_focus)
            if 1 <= game_focus <= counter - 1:
                getgameinfo(game_info[game_focus])
            else:
                print("Invalid selection. Please try again.\n")
        except ValueError:
            print("Invalid input. Please enter a valid game number, 'back', 'next', or 'exit'.\n")

def getgameinfo(dicta):
    global gamestarted
    global signal
    game_id = dicta['game_id']
    game_info = statsapi.get('game', {'gamePk': game_id})
    away_pitch = getpitcherstats(dicta['away_pitcher'])
    home_pitch = getpitcherstats(dicta['home_pitcher'])
    awayera = away_pitch['stats'][0]['stats']['era']
    awaywins = away_pitch['stats'][0]['stats']['wins']
    awayloss = away_pitch['stats'][0]['stats']['losses']
    homeera = home_pitch['stats'][0]['stats']['era']
    homewins = home_pitch['stats'][0]['stats']['wins']
    homeloss = home_pitch['stats'][0]['stats']['losses']
    print("\n")
    print(f"Away Starting Pitcher: {away_pitch['first_name']} \"{away_pitch['nickname']}\" {away_pitch['last_name']}:\t {awaywins}-{awayloss}, ERA = {awayera}" if away_pitch['nickname'] != None else f"Away Pitcher: {away_pitch['first_name']} {away_pitch['last_name']}:\t {awaywins}-{awayloss}, ERA = {awayera}")
    print(f"Home Starting Pitcher: {home_pitch['first_name']} \"{home_pitch['nickname']}\" {home_pitch['last_name']}:\t {homewins}-{homeloss}, ERA = {homeera}" if home_pitch['nickname'] != None else f"Home Pitcher: {home_pitch['first_name']} {home_pitch['last_name']}:\t {homewins}-{homeloss}, ERA = {homeera}")
    print("\n")
    getlinescore(game_id)
    print("\n")
    if dicta['status'] == "Final":
        getboxscore(game_id)
    #ADD THREAD TO LISTEN FOR NEW PLAYS
    #listening()
    while signal['shutdown'] == False:
        inp = input("Type Return to go back to the slate, type Box to see the boxscore, or type score to see all scoring plays. Type play to enter Play-by-play. ")
        print("\n")
        inp = inp.lower()
        if inp == 'return':
            slate()
        if inp == 'box':
            getboxscore(game_id)
        if inp == 'score':
            print( f"{statsapi.game_scoring_plays(game_id)}\n" )

        if inp == 'play':
            message_dict = json.dumps({
                "message_type": "INITIALIZE",
                "game_id": game_id,
            })
            tcp_client('localhost', 4391, message_dict)
            gamestarted = True
            while signal['shutdown'] == False and gamestarted:
                time.sleep(1)
        if inp == 'test':
                fig, ax = plt.subplots()
                x_left, x_right = -0.83, 0.83
                y_bottom, y_top = 1.5, 3.5
                width = (x_right - x_left) / 3  # Width of each zone
                height = (y_top - y_bottom) / 3  # Height of each zone
                
                # Zones order: [topleft, topmiddle, topright, middleleft, center, middleright, bottomleft, bottommiddle, bottomright]
                zones = [
                    (x_left, y_top - height),      # Top left
                    (x_left + width, y_top - height),  # Top middle
                    (x_left + 2 * width, y_top - height),  # Top right
                    (x_left, y_top - 2 * height),  # Middle left
                    (x_left + width, y_top - 2 * height),  # Center
                    (x_left + 2 * width, y_top - 2 * height),  # Middle right
                    (x_left, y_bottom),            # Bottom left
                    (x_left + width, y_bottom),    # Bottom middle
                    (x_left + 2 * width, y_bottom) # Bottom right
                ]
                colors = ['red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red',] #CHANGE THIS TO THE DATA COLORS LATER
                # Draw each of the 9 zones with the corresponding color
                for i, (x, y) in enumerate(zones):
                    rect = plt.Rectangle((x, y), width, height, facecolor=colors[i], edgecolor='black', linewidth=1)
                    ax.add_patch(rect)
                ax.set_xlim(-1, 1)
                ax.set_ylim(1, 4)
                ax.set_aspect('equal', 'box') 
                ax.axis('off')
                ax.set_title('Strike Zone v0.1')
                plt.show(block=False)

        time.sleep(.2)



def respond(message):
    global gamestarted
    global signal 
    #respond to message
    if message['message_type'] == 'shutdown':
        signal['shutdown'] = True
    if message['message_type'] == 'NOTSTARTED':
        gamestarted = False
    if message['message_type'] == 'PLAY':
        print(f"{message['event']}\n")
    if message['message_type'] == 'inning':
        getlinescore((message['message']))
        print("\n")



def getboxscore(gameid):
    print(statsapi.boxscore(gameid))

def getlinescore(gameid):
    print(statsapi.linescore(gameid))

def gethighlights(gameid):
    print(statsapi.game_highlights(gameid))

def getpitcherstats(fullname):
    player = statsapi.lookup_player(fullname)
    personId = (player[0]['id'])
    return statsapi.player_stat_data(personId, group="[pitching]", type="season", sportId=1)

def shutdown():
    exit
    
main()