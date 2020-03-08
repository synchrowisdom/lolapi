'''


Examples using the LolApi Python wrapper.
For more info about the API service, consult 
https://developer.riotgames.com/getting-started.html.

NB: It only supports the 'NA' region at this time.


'''


from LolApi import LolApi
import json


# Configure your API key here and initialize the class.
api = LOLAPI('Your developper API key')
summonerName = 'ASummonerName'

# Display some documentation about each functions.
api.showhelp()

# Get the summoner information.
status_code, text = api.get_summonerbyname(summonerName)
if status_code == 200:    
    summoner = json.loads(text)
    print('get_summonerbyname:')
    print(json.dumps(summoner, indent=4))
    print('')
else:
    # Something went wrong, is this summoner name valid?
    print('Couldn\'t retrieve this summoner\'s information. Please check the summoner name and retry (NA region only).')
    exit(-1)


# Get the current match information for 
#   a particular summonerId. PS: Summoner must be
#   in-game.
status_code, text = api.get_currentmatch(summoner['id'])
if status_code == 200:   
    currentmatch = json.loads(text)
    participants = currentmatch['participants']
    print('get_currentmatch:')
    print(json.dumps(participants, indent=4))
    print('')
    
    # Pull the list of summoner as well as the summonerId they are currently playing.
    print('get_currentmatch summonerName and summonerId:')
    for p in participants:
        print(p['summonerName'], p['summonerId'])
    print('')
else:
    # Something went wrong, is this summoner in a game right now?
    print('Couldn\'t retrieve the current game for this summoner.')


# Get the recent matches list for
#   a particular accountid.
status_code, text = api.get_recentmatches(summoner['accountId'])
if status_code == 200:
    recentmatches = json.loads(text)
    print('get_recentmatches:')
    print(json.dumps(recentmatches, indent=4))
    print('')
else:
    # Something went wrong, is this summoner valid or perhaps never played yet.
    print('Couldn\'t retrive recent matches for this summoner.')

 # Display the LolApi stats for our usage
 print(api.get_apistats())
