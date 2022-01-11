'''
Created on Jun 27, 2021

@author: willg
'''

#Exceptions having to do with a lack of authority
class NotAuthorized(Exception):
    pass

class NoAuthorityWithTableBot(NotAuthorized):
    pass

class NotBadWolf(NoAuthorityWithTableBot):
    pass

class NotBotAdmin(NoAuthorityWithTableBot):
    pass

class NoAuthorityInServer(NotAuthorized):
    pass

class NotServerAdministrator(NoAuthorityInServer):
    pass

class NotStaff(NoAuthorityInServer):
    pass

class NotLoungeStaff(NotStaff):
    pass


class WrongServer(NotAuthorized):
    pass

class WrongChannel(NotAuthorized):
    pass

class WrongUpdaterChannel(WrongChannel):
    pass

class NotLoungeServer(WrongServer):
    pass


#Coding errors
class UnreachableCode(Exception):
    pass

class BlacklistedUser(NotAuthorized):
    pass
class WarnedUser(NotAuthorized):
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


class CommandDisabled(Exception):
    pass

class WiimmfiSiteFailure(Exception):
    pass

