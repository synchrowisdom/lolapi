import requests
import time


class LOLAPI():
    '''
    As simple as it can get Python
    wrapper for the LoL API service.
    ''' 

    # Lol API URLs.
    _API_serverurl = (['https://na1.api.riotgames.com', 'NA'])
    _API_summonerbyname = '/lol/summoner/v3/summoners/by-name/{summonerName}'
    _API_getcurrentmatch = '/lol/spectator/v3/active-games/by-summoner/{summonerId}'
    _API_recentmatches = '/lol/match/v3/matchlists/by-account/{accountId}'

    # API calls' limits
    _LIMIT_perseconds = 20
    _LIMIT_perminutes = 100
    # API call trackers - Not accurate, they are refreshed only when _pullfromapi() is used.
    _lastapicalltimer = time.perf_counter()      
    _currentapicalls_persec = 0
    _currentapicalls_permin = 0


    def __init__(self, apikey, region='NA'):
        '''
        API key provided by Riot. For more information about this
            consult https://developer.riotgames.com/api-keys.html.
        
        region will default to NA if not specified.
            For a list of valid values, consult 
            https://developer.riotgames.com/regional-endpoints.html.
        '''
        
        # Save our variables
        self.apikey = apikey
        self.region = region
        return

        
    def _formurlforcall(self, url, accountid=None, matchid=None, summonerid=None, summonername=None):
        '''
        Returns a configured URL string from the provided
            parameters values and base call URL.
        '''

        # List of parameters that can be used for the API calls.
        apiparameters = {'{accountId}' : accountid,
                         '{matchId}' : matchid,
                         '{summonerId}' : summonerid,
                         '{summonerName}' : summonername}

        apiparameters['{accountId}'] = accountid
        apiparameters['{matchId}'] = matchid
        apiparameters['{summonerId}'] = summonerid
        apiparameters['{summonerName}'] = summonername

        # Make sure that every parameters present in the URL
        #   has been provided.
        for p, v in apiparameters.items():
            if p in url:                
                if v is None:
                    print('Error in _formurlforcall! {parametername} was found in the URL but not provided.'.replace('{parametername}', p))
                    return None
                else:
                    url = url.replace(p, str(v))
                    
        # Return the configured URL.
        return self._API_serverurl[0] + url + '?api_key=' + self.apikey
    

    def _pullfromapi(self, url, callbackname, asyncop=False):
        '''
        Calls the API and returns a status_code for
            the operation as well as a JSON text.
            
            Set asyncop=True to have this function exit
                rather than to block and wait.

            Returns status_code, text (JSON).
        '''

        # Reset our current API call counter if needed.
        t = time.perf_counter() - self._lastapicalltimer
        if t > 60:
            self._currentapicalls_persec = 0
            self._currentapicalls_permin = 0
        elif t > 1:
            self._currentapicalls_persec = 0

        # Check for API rate limits.
        busted_persec = True if self._currentapicalls_persec >= self._LIMIT_perseconds else False
        busted_permin = True if self._currentapicalls_permin >= self._LIMIT_perminutes else False
        if (busted_persec or busted_permin):        
            print(f'Error with the API call for {callbackname}! API calls per seconds or minutes limit reached [{self._currentapicalls_persec}/{self._LIMIT_perseconds}] [{self._currentapicalls_permin}/{self._LIMIT_perminutes}]')
            print('Throttling...')
            
            # Don't throttle if async=True
            if asyncop == True:
                return -1, None

            t = 60 if busted_permin else 1  # Time needing to wait.
            while (time.perf_counter() - self._lastapicalltimer) <= t:
                time.sleep(.1)

            # Reset the required counters.
            if busted_permin:
                self._currentapicalls_permin = 0
                self._currentapicalls_persec = 0             
            else:
                self._currentapicalls_persec = 0


        # Reset our last API call timer and increment our counters.
        self._lastapicalltimer = time.perf_counter()
        self._currentapicalls_persec += 1
        self._currentapicalls_permin += 1
         
        r = requests.get(url)
        if r.status_code != 200:
            print('Error with the API call for {callbackname}! Call failed for some reason. status_code={status_code}'.format(callbackname = callbackname,
                                                                                                                           status_code = r.status_code))
            print('Please consult https://developer.riotgames.com/response-codes.html for more information.')
        # Return our result
        return r.status_code, r.text


    def get_summonerbyname(self, summonername):
        '''
        Retrieve information for a particular summoner.
            Returns status_code, text (JSON).
            
        Use output= to redirect the output to this location
            rather than by using the standard return.
        '''
        url = self._formurlforcall(url=self._API_summonerbyname, summonername=summonername)
        status_code, text = self._pullfromapi(url, 'get_summonerbyname')   
        return status_code, text
       

    def get_currentmatch(self, summonerid):
        '''
        Retrieve the current match information for
            a specific summonerid.

            Returns status_code, text (JSON).
        '''
        url = self._formurlforcall(url=self._API_getcurrentmatch, summonerid = summonerid)
        status_code, text = self._pullfromapi(url, 'get_currentmatch')
        return status_code, text

    def get_recentmatches(self, accountid):
        '''
        Retrieves a list of matches for a
            specific accountid.

            Returns status_code, text (JSON).
        '''
        url = self._formurlforcall(url=self._API_recentmatches, accountid = accountid)
        status_code, text = self._pullfromapi(url, 'get_recentmatches')
        return status_code, text
