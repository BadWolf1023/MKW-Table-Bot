'''
Created on Jun 27, 2021

@author: willg
'''

#Exceptions having to do with a lack of authority
class NotAuthorized(Exception):
    pass

class NotBadWolf(NotAuthorized):
    pass

class NotBotAdmin(NotAuthorized):
    pass

class NotServerAdministrator(NotAuthorized):
    pass

class NotLoungeStaff(NotAuthorized):
    pass



class WarSetupFailure(Exception):
    pass
#Exceptions that might be thrown when war is started
class InvalidWarFormatException(WarSetupFailure):
    pass

class InvalidNumberOfPlayersException(WarSetupFailure):
    pass

class WarSetupStillRunning(WarSetupFailure):
    pass
