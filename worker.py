#code
import threading
import statsapi
import time
import json
import queue
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from network import tcp_server, udp_server, tcp_client, udp_client



def main():
    global signal
    signal = {'shutdown': False}
    global tcp_thread
    tcp_thread = threading.Thread(target=tcp_server, args=('localhost', 4391, signal, lambda message: respond(message),), name="tcp_server")
    tcp_thread.daemon = True  # Set as daemon so the thread will exit when the main program exits
    tcp_thread.start()
    host = 1
    # Initialize and start the udp_server thread
    while signal["shutdown"] == False:
        time.sleep(1)

def respond(message):
    global signal
    print(f"Received message: {message}")
    if message["message_type"] == "INITIALIZE":
        print("WORKER INITIALIZED")
        game_id = message['game_id']
        working = threading.Thread(target=getplaybyplay, args=(game_id,), name="worker")
        working.start()
        
    if message['message_type'] == "shutdown":
        signal['shutdown'] = True
        tcp_thread.join()
        exit()

def getplaybyplay(game_id):
    global signal
    last = ""
    balls = 0
    strikes = 0
    outs = 0
    batter = ""
    pitcher = ""
    lastbatter= ""
    lastpitcher = ""
    lastballs = -1
    laststrikes = -1
    lastouts = -1
    counter = -2
    lastplayevent = "" #MAY NEED TO ADD SOMETHING IF MULTIPLE IN PLAY THINGS OCCUR
    lastpitchindexsize = 0
    fig, ax = plt.subplots(figsize=(10,8))
    plt.ion()
    while signal["shutdown"] == False:
        playbyplay = statsapi.get('game_playByPlay', {'gamePk': game_id})
        try: current_play = playbyplay['currentPlay']
        except: 
            print("Game not started")
            message_dict = json.dumps({
                "message_type": "NOTSTARTED",
            })
            tcp_client('localhost', 4390, message_dict)
            return
        balls = current_play['count']['balls']
        strikes = current_play['count']['strikes']
        outs = current_play['count']['outs']
        batter = current_play['matchup']['batter']['fullName']
        pitcher = current_play['matchup']['pitcher']['fullName']
        pitchindexsize = len(current_play['pitchIndex'])
        # Check if this is a new batter
        #print(json.dumps(current_play, indent=2))
        if lastbatter != batter or lastpitcher != pitcher:
            #if laststrikes == 2 and playbyplay['allPlays'][-1]['result']['event'] == 'strikeout':
            #    message_dict = json.dumps({
            #        "message_type": "PLAY",
            #        "event": f"{playbyplay['allPlays'][-1]['result']['description']}. {lastbatter} strikes out, {outs} out(s)",
            #    })
            #    tcp_client('localhost', 4390, message_dict)
            #elif lastballs == 3 and playbyplay['allPlays'][-1]['result']['event'] == 'walk':
            #    message_dict = json.dumps({
            #        "message_type": "PLAY",
            #        "event": f"{playbyplay['allPlays'][-1]['result']['description']}. {lastbatter} walks, {outs} out(s)",
            #    })
            #    tcp_client('localhost', 4390, message_dict)
            lastbatter = batter
            lastballs = balls
            laststrikes = strikes
            lastouts = outs
            lastpitchindexsize = 0
            lastplayevent = ""
            lastpitcher = pitcher
            #print(json.dumps(current_play['matchup']['batterHotColdZones'], indent=2))
            colors = current_play['matchup']['batterHotColdZones']
            message_dict = json.dumps({
                "message_type": "PLAY",
                "event": f"Now Batting: {batter}, Pitching: {pitcher} ---- {outs} out(s)",
            })
            tcp_client('localhost', 4390, message_dict)
            #print(f"Now Batting: {batter}, Pitching: {pitcher} ---- {outs} out(s)")
            ax.cla()
            create_zone(ax, batter, pitcher, colors)
            if counter>=-1:
                counter+=1

        # Check if the count has changed for the same batter

        #TO DO LIST 
        #PRINT THE IN PLAY STUFF WHEN THEY GET DESCRIPTIONS
        #PRINT STRIKOUTS
        #PRINT MULTIPLE FOULS IN A ROW
        elif lastballs != balls or laststrikes != strikes: #new pitch
            
            if len(current_play['playEvents']) > 0:
                event = current_play['playEvents'][-1]['details']['description']
                last_event = current_play['playEvents'][-1] #FOULS LOOK THE SAME SO IT DOESNT GET PRINTED AGAIN
                lastplayevent = event
                
                if strikes == 3:
                    message_dict = json.dumps({
                        "message_type": "PLAY",
                        "event": f"{event}. {batter} strikes out, {outs} out(s)",
                    })
                    tcp_client('localhost', 4390, message_dict)
                    print(json.dumps(last_event['details']))
                    x = last_event['pitchData']['coordinates']['pX']
                    y = last_event['pitchData']['coordinates']['pZ']
                    add_pitch(ax, x, y, 'strike')
                    #print(f"{event}. {batter} strikes out, {outs} out(s)")
                elif balls == 4:
                    message_dict = json.dumps({
                        "message_type": "PLAY",
                        "event": f"{event}. {batter} walks, {outs} out(s)",
                    })
                    tcp_client('localhost', 4390, message_dict)
                    print(json.dumps(last_event['details']))
                    x = last_event['pitchData']['coordinates']['pX']
                    y = last_event['pitchData']['coordinates']['pZ']
                    add_pitch(ax, x, y, 'ball')
                   # print (f"{event}. {batter} walks, {outs} out(s)")
                
                else:
                    message_dict = json.dumps({
                        "message_type": "PLAY",
                        "event": f"{event}. The count is {balls}-{strikes}, {outs} out(s)",
                    })
                    tcp_client('localhost', 4390, message_dict)
                    print(json.dumps(last_event['details']))
                    if 'pitchData' in last_event:
                        x = last_event['pitchData']['coordinates']['pX']
                        y = last_event['pitchData']['coordinates']['pZ']
                        if last_event['details']['isStrike']:
                            add_pitch(ax, x, y,'strike')
                        else:
                            add_pitch(ax, x, y, 'ball')
                    #print(f"{event}. The count is {balls}-{strikes}, {outs} out(s)")
            #add adding pitches here
            lastballs = balls
            laststrikes = strikes
            
            lastpitchindexsize = pitchindexsize

        elif len(current_play['playEvents']) > 0: #NOT SEEINGS THE IN PLAY
            last_event = current_play['playEvents'][-1]

            if last_event['details']['description'] != lastplayevent or lastpitchindexsize != pitchindexsize:
                event = last_event['details']['description']
                #if event = foul add to the graph
                #print(json.dumps(current_play, indent=2))
                if 'In play' in event:
                    message_dict = json.dumps({
                        "message_type": "PLAY",
                        "event": f"{event}.",
                    })
                    tcp_client('localhost', 4390, message_dict)
                    counter = -1
                    print(json.dumps(last_event['details']))
                    x = last_event['pitchData']['coordinates']['pX']
                    y = last_event['pitchData']['coordinates']['pZ']
                    add_pitch(ax, x, y, 'inplay')
                    #time.sleep(2)
                    playstartTime = current_play['about']['startTime']
                    descriptor = statsapi.get('game_playByPlay', {'gamePk': game_id})
                    all_plays = descriptor .get('allPlays', [])
                    specific_play = next((play for play in all_plays[-3:] if play['about']['startTime'] == playstartTime), None)
                    while 'description' not in specific_play['result']: # how do i get it to only look at the correct play - look for an identifier
                        # and 'description' not in descriptor['allPlays'][-2]['result']: #DOESNT SEE THE CORRECT EVENT - GOES TO A DIFFERENT PLAY
                        descriptor = statsapi.get('game_playByPlay', {'gamePk': game_id})
                        all_plays = descriptor .get('allPlays', [])
                        specific_play = next((play for play in all_plays[-3:] if play['about']['startTime'] == playstartTime), None)
                        print(json.dumps(descriptor['allPlays'][-1], indent=2))
                        time.sleep(3)
                    message_dict = json.dumps({
                        "message_type": "PLAY",
                        "event": f"{specific_play['result']['description']}",
                    })
                    tcp_client('localhost', 4390, message_dict)
                else:
                    message_dict = json.dumps({
                        "message_type": "PLAY",
                        "event": f"{event}. The count is {balls}-{strikes}, {outs} out(s)",
                    })
                    tcp_client('localhost', 4390, message_dict)
                
                #print(f"{event}. The count is {balls}-{strikes}, {outs} out(s)")
                lastplayevent = event
                lastpitchindexsize = pitchindexsize                    

                if 'Foul' in event:
                    x = last_event['pitchData']['coordinates']['pX']
                    y = last_event['pitchData']['coordinates']['pZ']
                    add_pitch(ax, x, y, 'foul')
            
        
        if outs == 3 and lastouts != 3:
            message_dict = json.dumps({
                    "message_type": "inning",
                    "event": f"Inning Over\n",
                    "message": game_id
            })
            tcp_client('localhost', 4390, message_dict)
            time.sleep(115)
        lastouts = outs
            #print("Inning Over")
            #getlinescore(game_id)
                #fix to change to score later
                #if its a new batter print the last event (Now batting - pitchig - outs)
                #if its the same batter but the same count dont print anything (UNLESS A NEW EVENT OCCURS)
                #if its the same batter but different count print the call and the new count
                
                #lastplay = playbyplay['allPlays'][-1]
                #description = lastplay['result']['description']
                #away_score = lastplay['result']['awayScore']
                #home_score = lastplay['result']['homeScore']
            
                #event = last['playEvents'][-1]['details']['description'] #call?
                
                #print(f"{description}. The score is {away_score}-{home_score}")

                #print(event + f". The count is {balls}-{strikes}, {outs} out(s)")

            

        time.sleep(1)

def create_zone(ax, batter, pitcher, colors):  
                # Draw the strike zone
    # Strike zone boundaries
    if colors==[]:
        colors = [
            {'color': 'white'}, {'color': 'white'}, {'color': 'white'},        # Top row (zones 1-3)
            {'color': 'white'}, {'color': 'white'}, {'color': 'white'},        # Middle row (zones 4-6)
            {'color': 'white'}, {'color': 'white'}, {'color': 'white'},  
            {'color': 'white'}, {'color': 'white'}, {'color': 'white'},       # Bottom row (zones 7-9)
        ]
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
    # Draw each of the 9 zones with the corresponding color
    for i, (x, y) in enumerate(zones):
        rgba_values = colors[i]['color'].replace('rgba(', '').replace(')', '').split(',')
        r = int(rgba_values[0].strip()) / 255.0
        g = int(rgba_values[1].strip()) / 255.0
        b = int(rgba_values[2].strip()) / 255.0
        a = float(rgba_values[3].strip())

        rgba_color = (r, g, b, a)
        rect = plt.Rectangle((x, y), width, height, facecolor=rgba_color, edgecolor='black', linewidth=1)
        ax.add_patch(rect)

    ax.set_xlim(-4, 4)
    ax.set_ylim(-2, 7)
    ax.set_aspect('equal', 'box') 
    ax.axis('off')
    ax.set_title(f'Batting: {batter} ---- Pitching: {pitcher}')
    plt.draw()
    plt.pause(0.001)

def add_pitch(ax, xcoord, ycoord, types):
    color = ""
    if types == 'strike':
        color='red'
    elif types == 'ball':
        color='green'
    elif types == 'inplay':
        color='blue'
    elif types == 'foul':
        color='grey'
    print(xcoord)
    print(ycoord)
    ax.scatter(xcoord, ycoord, s=300, c=color, zorder=3)
    plt.draw()
    plt.pause(0.001)


def getlinescore(gameid):
    print(statsapi.linescore(gameid))

main()