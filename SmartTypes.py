import UtilityFunctions
import UserDataProcessing
import LoungeAPIFunctions
from typing import List, Union

class SmartLookupTypes:
    FC = object()
    FC_LIST = object()
    DISCORD_ID = object()
    SELF_DISCORD_ID = object()
    MIN_DISCORD_ID = 4194304
    MAX_DISCORD_ID = 18446744073709551615
    RXX = object()
    LOUNGE_NAME = object()
    RAW_DISCORD_MENTION = object()
    UNKNOWN = object()
    ALL_TYPES = {FC, FC_LIST, SELF_DISCORD_ID, DISCORD_ID, RXX, LOUNGE_NAME, RAW_DISCORD_MENTION, UNKNOWN}
    PLAYER_LOOKUP_TYPES = {FC, FC_LIST, SELF_DISCORD_ID, DISCORD_ID, LOUNGE_NAME, RAW_DISCORD_MENTION}
    ROOM_LOOKUP_TYPES = {RXX} | PLAYER_LOOKUP_TYPES
    
    def __init__(self, data, allowed_types=None):
        self.original = data
        self.modified_original = data
        self._original_type = SmartLookupTypes.UNKNOWN
        self._allowed_types = SmartLookupTypes.ALL_TYPES if allowed_types is None else allowed_types
        if isinstance(self.modified_original, str):
            self.modified_original = self.modified_original.strip().lower()
            if SmartLookupTypes.FC in self._allowed_types and UtilityFunctions.is_fc(data):
                self._original_type = SmartLookupTypes.FC
            elif SmartLookupTypes.RXX in self._allowed_types and UtilityFunctions.is_rLID(data):
                self._original_type = SmartLookupTypes.RXX
            elif SmartLookupTypes.DISCORD_ID in self._allowed_types and UtilityFunctions.is_int(data) and int(data) >= SmartLookupTypes.MIN_DISCORD_ID and int(data) <= SmartLookupTypes.MAX_DISCORD_ID:
                self._original_type = SmartLookupTypes.DISCORD_ID
            elif SmartLookupTypes.RAW_DISCORD_MENTION in self._allowed_types and UtilityFunctions.is_discord_mention(data):
                self._original_type = SmartLookupTypes.RAW_DISCORD_MENTION
                self.modified_original = self.modified_original.strip('<>@! ')
            elif SmartLookupTypes.LOUNGE_NAME in self._allowed_types and len(data) > 0:
                self._original_type = SmartLookupTypes.LOUNGE_NAME
        elif isinstance(data, int):
            if SmartLookupTypes.DISCORD_ID in self._allowed_types and int(data) >= SmartLookupTypes.MIN_DISCORD_ID and int(data) <= SmartLookupTypes.MAX_DISCORD_ID:
                self._original_type = SmartLookupTypes.DISCORD_ID
                self.modified_original = str(self.modified_original).strip()
            elif SmartLookupTypes.LOUNGE_NAME in self._allowed_types and len(str(data)) > 0:
                self._original_type = SmartLookupTypes.LOUNGE_NAME
                self.modified_original = str(self.modified_original).strip()
        elif isinstance(data, list):
            if SmartLookupTypes.FC_LIST in self._allowed_types and all(isinstance(d, str) for d in data) and all(UtilityFunctions.is_fc(d) for d in data):
                self._original_type = SmartLookupTypes.FC_LIST
        elif isinstance(data, set):
             if SmartLookupTypes.FC_LIST in self._allowed_types and all(isinstance(d, str) for d in data) and all(UtilityFunctions.is_fc(d) for d in data):
                self._original_type = SmartLookupTypes.FC_LIST
                self.modified_original = list(self.modified_original)
        elif isinstance(data, tuple):
            if SmartLookupTypes.SELF_DISCORD_ID in self._allowed_types:
                if len(data) == 2 and data == create_you_discord_id(data[1]):
                    self.modified_original = data[1]
                    self._original_type = SmartLookupTypes.SELF_DISCORD_ID

    def add_allowed_type(self, type_):
        if type_ not in SmartLookupTypes.ALL_TYPES:
            raise ValueError("Invalid lookup type addition")
        self._allowed_types.add(type_)

    def remove_allowed_type(self, type_):
        if type_ in self._allowed_types:
            self._allowed_types.remove(type_)

    def is_invalid_type(self, type_=None):
        type_ = self._original_type if type_ is None else type_
        return type_ in self._allowed_types

    def get_type(self):
        return self._original_type

    def get_country_flag(self, suppress_exception=False) -> Union[str, None]:
        return UserDataProcessing.get_flag(self.get_discord_id())

    def get_discord_id(self, suppress_exception=False) -> Union[int, None]:
        if self._original_type not in SmartLookupTypes.PLAYER_LOOKUP_TYPES:
            if suppress_exception:
                return None
            raise ValueError("Cannot get discord id for unsupported type")
        discord_id = None
        if self._original_type is SmartLookupTypes.FC:
            discord_id = UserDataProcessing.get_discord_id_from_fc(self.modified_original)
        elif self._original_type is SmartLookupTypes.FC_LIST:
            for fc in self.modified_original:
                discord_id = UserDataProcessing.get_discord_id_from_fc(fc)
                if discord_id is not None and discord_id != '':
                    break
        elif self._original_type is SmartLookupTypes.DISCORD_ID or self._original_type is SmartLookupTypes.RAW_DISCORD_MENTION or self._original_type is SmartLookupTypes.SELF_DISCORD_ID:
            discord_id = self.modified_original
        elif self._original_type is SmartLookupTypes.LOUNGE_NAME:
            discord_id = UserDataProcessing.get_DiscordID_By_LoungeName(self.modified_original)

        return None if discord_id == '' else discord_id


    def get_lounge_name(self, suppress_exception=False) -> Union[str, None]:
        if self._original_type not in SmartLookupTypes.PLAYER_LOOKUP_TYPES:
            if suppress_exception:
                return None
            raise ValueError("Cannot get lounge name for unsupported type")
        lounge_name = None
        if self._original_type is SmartLookupTypes.FC:
            lounge_name = UserDataProcessing.lounge_get(self.modified_original)
        elif self._original_type is SmartLookupTypes.FC_LIST:
            for fc in self.modified_original:
                lounge_name = UserDataProcessing.lounge_get(fc)
                if lounge_name is not None and lounge_name != '':
                    break
        elif self._original_type is SmartLookupTypes.DISCORD_ID or self._original_type is SmartLookupTypes.RAW_DISCORD_MENTION or self._original_type is SmartLookupTypes.SELF_DISCORD_ID:
            lounge_name = UserDataProcessing.get_lounge(self.modified_original)
        elif self._original_type is SmartLookupTypes.LOUNGE_NAME:
            lounge_name = self.modified_original

        return None if lounge_name == '' else lounge_name

    def get_fcs(self, suppress_exception=False) -> Union[List[str], None]:
        if self._original_type not in SmartLookupTypes.PLAYER_LOOKUP_TYPES:
            if suppress_exception:
                return None
            raise ValueError("Cannot get fcs for unsupported type")
        fcs = []
        if self._original_type is SmartLookupTypes.FC:
            fcs = [self.modified_original]
        elif self._original_type is SmartLookupTypes.FC_LIST:
            fcs = self.modified_original
        elif self._original_type is SmartLookupTypes.DISCORD_ID or self._original_type is SmartLookupTypes.RAW_DISCORD_MENTION or self._original_type is SmartLookupTypes.SELF_DISCORD_ID:
            fcs = UserDataProcessing.get_all_fcs(self.modified_original)
        elif self._original_type is SmartLookupTypes.LOUNGE_NAME:
            fcs = UserDataProcessing.getFCsByLoungeName(self.modified_original)
        
        return None if (fcs is None or len(fcs) == 0) else fcs

    async def lounge_api_update(self, suppress_exception=False):
        if self._original_type not in SmartLookupTypes.PLAYER_LOOKUP_TYPES:
            if suppress_exception:
                return None
            raise ValueError("Cannot hit Lounge API for unsupported type")

        if self._original_type is SmartLookupTypes.FC:
            UserDataProcessing.smartUpdate(* await LoungeAPIFunctions.getByFCs([self.modified_original]))
        elif self._original_type is SmartLookupTypes.FC_LIST:
            UserDataProcessing.smartUpdate(* await LoungeAPIFunctions.getByFCs(self.modified_original))
        elif self._original_type is SmartLookupTypes.DISCORD_ID or self._original_type is SmartLookupTypes.RAW_DISCORD_MENTION or self._original_type is SmartLookupTypes.SELF_DISCORD_ID:
            UserDataProcessing.smartUpdate(* await LoungeAPIFunctions.getByDiscordIDs([self.modified_original]))
        elif self._original_type is SmartLookupTypes.LOUNGE_NAME:
            UserDataProcessing.smartUpdate(* await LoungeAPIFunctions.getByLoungeNames([self.modified_original]))
        return True

    def is_rxx(self):
        return self._original_type is SmartLookupTypes.RXX

def create_you_discord_id(discord_id):
    return ("you", str(discord_id))