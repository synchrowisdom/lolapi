import requests
import time


class LolApi():
    '''
    As simple as it can get Python
    wrapper for the LoL API service.
    ''' 

    # Lol API URLs.
    _API_serverurl = (['https://na1.api.riotgames.com', 'NA'])
    _API_summonerbyname = '/lol/summoner/v3/summoners/by-name/{summonerName}'
    _API_getcurrentmatch = '/lol/spectator/v3/active-games/by-summoner/{summonerId}'
    _API_recentmatches = '/lol/match/v3/matchlists/by-account/{accountId}'
    _API_matchinfo = '/lol/match/v3/matches/{matchId}'    

    # API calls' limits and cooldowns to wait when throtling.
    _LIMIT_perseconds = 20
    _LIMIT_perminutes = 100
    _COOLDOWN_forsecondsbusted = 1
    _COOLDOWN_forminutesbusted = 20
    _COOLDOWN_default = 30 # Default cooldown timer for API errors.
    
    # API call trackers - Not accurate, they are refreshed only when _pullfromapi() is used.
    _nextavailable_apicall = time.perf_counter()
    _minutetimer = None
    _currentapicalls_persec = 0
    _currentapicalls_permin = 0
    _total_apicall = 0
    _total_apicallerror = 0
    _total_statuscode429 = 0 # Status code 429 are indicating an overflow of calls and should be avoided.


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

    def showhelp(self):
        '''
        Display the documentation about each functions.
        '''        
        print('LolApi(apikey=, region=\'NA\')')
        print(self.__init__.__doc__)
        print('')
        print('get_summonerbyname(summonername=)')
        print(self.get_summonerbyname.__doc__)
        print('')
        print('get_currentmatch(summonerid=)')
        print(self.get_currentmatch.__doc__)
        print('')
        print('get_recentmatches(accountid=, championid=None, beginindex=None, endindex=None)')
        print(self.get_recentmatches.__doc__)
        print('')
        print('get_matcheinfo(matchid=)')
        print(self.get_matchinfo.__doc__)        
        return

    def get_apistats(self):
        '''
        Display stats related to this LoL API instance.
        '''

        stats = {
            '_nextavailable_apicall':self._nextavailable_apicall,
            '_minutetimer':self._minutetimer,
            '_currentapicalls_persec':self._currentapicalls_persec,
            '_currentapicalls_permin':self._currentapicalls_permin,
            '_total_apicall':self._total_apicall,
            '_total_apicallerror':self._total_apicallerror,
            '_total_statuscode429':self._total_statuscode429 }
        return stats
        
    def _formurlforcall(self, url, accountid=None, matchid=None, summonerid=None,
                        summonername=None, beginindex=None, endindex=None, championid=None):
        '''
        Returns a configured URL string from the provided
            parameters values and base call URL.
        '''

        # List of parameters that can be used for the API calls.
        apiparameters = {'{accountId}' : accountid,
                         '{matchId}' : matchid,
                         '{summonerId}' : summonerid,
                         '{summonerName}' : summonername,
                         '{beginIndex}' : beginindex,
                         '{endIndex}' : endindex,
                         '{champion}' : championid,
                        }
        
        if accountid is not None:
            apiparameters['{accountId}'] = accountid
        if matchid is not None:
            apiparameters['{matchId}'] = matchid 
        if summonerid is not None:
            apiparameters['{summonerId}'] = summonerid
        if summonername is not None:
            apiparameters['{summonerName}'] = summonername
        if beginindex is not None:
            apiparameters['{beginIndex}'] = beginindex
        if endindex is not None:
            apiparameters['{endIndex}'] = endindex
        if championid is not None:
            apiparameters['{champion}'] = championid
                
        # Initialize the URL.
        mainparameter = url[url.find('{'):url.find('}') + 1]
        tempurl = self._API_serverurl[0] + url.replace(mainparameter, str(apiparameters[mainparameter]))
        del apiparameters[mainparameter]    # Remove this entry from the parameter list.
        paramcount = 1  # At this point, we have 1 parameter attached (ie: our main parameter).
        
        # Parse through the list of parameters and form the URL while 
        #   keeping track of how many parameters are used. The first parameter
        #   requires nothing special but then the second requires ? in front
        #   and & for subsequent ones.
        for p, v in apiparameters.items():
            # Generate the proper linking character for the next parameter.            
            if paramcount == 1:
                link = '?'                    
            else:
                link = '&'
                               
            if v is None:
                pass
            else:                                                                                
                # Attach this parameter and increase our parameter counter.                      
                tempurl += (link + p[1:-1] + '=') + str(v)   #remove first and last character eg: {accountId}.
                paramcount += 1                
                        
        # Attach the API key and return the configured URL.
        tempurl += link + 'api_key=' + self.apikey
        return tempurl
    

    def _pullfromapi(self, url, callbackname, asyncop=False):
        '''
        Calls the API and returns a status_code for
            the operation as well as a JSON text.
            
            Set asyncop=True to have this function exit
                rather than to block and wait.

            Returns status_code, text (JSON).
        '''

        # Check if we are ready to make the next call        
        timer = time.perf_counter()        
        timerdelta = timer - self._nextavailable_apicall
        if self._minutetimer is None:
            self._minutetimer = timer
            
        if timerdelta < 0:                    
            # Cooldown period before making next call
            print(f'Error with the API call for {callbackname}! ' \
                  f'API calls per seconds or minutes limit reached '\
                  f'[{self._currentapicalls_persec}/{self._LIMIT_perseconds}] '\
                  f'[{self._currentapicalls_permin}/{self._LIMIT_perminutes}]  '\
                  f'[Timer delta: {timerdelta}].')
            print('Throttling...')
            
            # Don't throttle if async=True
            if asyncop == True:
                return -1, None

            # Throttle loop
            t = -1
            while (t < 0):
                t = time.perf_counter() - self._nextavailable_apicall
                time.sleep(.1)                      

            # Ajust our new timerdelta
            timerdelta = time.perf_counter() - timer
  
        # Reset our counter if needed.        
        if timerdelta > 1:
            self._currentapicalls_persec = 0
        if (time.perf_counter() - self._minutetimer) > 60:        
            self._currentapicalls_permin = 0
            self._minutetimer = None
        
        # Pull the data from the API         
        self._total_apicall += 1
        self._currentapicalls_persec += 1
        self._currentapicalls_permin += 1                
        r = requests.get(url)        
        timerajustment = 0 # Cooldown ajustment before the next call can be made
        if r.status_code != 200:
            print(r.headers) #debug
            self._total_apicallerror += 1
            timerajustment = self._COOLDOWN_default
            print('Error with the API call for {callbackname}! Status_code={status_code}'.format(
                callbackname = callbackname,
                status_code = r.status_code))
            print('Please consult https://developer.riotgames.com/response-codes.html '\
                  'for more information.')            

            if r.status_code == 429:
                self._total_statuscode429 += 1
                if 'Retry-After' in r.headers:
                    retryafter = int(r.headers['Retry-After'])
                else:
                    # Retry-After not found, it means that another API on top
                    #   of the LoL service is overloaded. Let's give it a breather.
                    #   https://discussion.developer.riotgames.com/questions/2299/rate-limit-exceeded-even-though-its-not.html
                    retryafter = 10

                timerajustment = retryafter
                                    
        # Check for API rate limits and set time of next available API call.        
        if timerajustment == 0: # Existing timerajustment superseeds
            if self._currentapicalls_persec >= self._LIMIT_perseconds:
                timerajustment = self._COOLDOWN_forsecondsbusted 
            if self._currentapicalls_permin >= self._LIMIT_perminutes:
                timerajustment = self._COOLDOWN_forminutesbusted

        # Adjust the next available API call timer if necessary
        self._nextavailable_apicall = time.perf_counter() + timerajustment                        
            
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


    def get_recentmatches(self, accountid, championid=None, beginindex=None, endindex=None):
        '''
        Retrieves a list of matches for a
            specific accountid (and championid if provided).

            maxmatchcount can be defined to limite the
                amount of to seek for. The default is 
                100 (defined by the LoL API itslef).

            Returns status_code, text (JSON).
        '''
        url = self._formurlforcall(url=self._API_recentmatches, accountid = accountid, championid = championid,
                                   beginindex = beginindex, endindex = endindex)
        status_code, text = self._pullfromapi(url, 'get_recentmatches')
        return status_code, text
        
        
    def get_matchinfo(self, matchid):
        '''
        Retrieve the information for a specific
            matchId.

            Returns status_code, text (JSON).
        '''
        url = self._formurlforcall(url=self._API_matchinfo, matchid = matchid)
        status_code, text = self._pullfromapi(url, 'get_matchinfo')
        return status_code, text
