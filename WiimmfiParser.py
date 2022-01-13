'''
Created on May 6, 2021

@author: willg
'''
    
import itertools
from typing import List
from collections import defaultdict

from bs4 import NavigableString
import bs4
from bs4.element import Tag

import common

import UserDataProcessing
import UtilityFunctions
import Race
import Player
import Placement


class RoomPageParser(object):
    '''
    classdocs
    '''
    DEBUG_RACES = False
    DEBUG_PLACEMENTS = False

    def __init__(self, soup):
        self._set_room_races(list())
        self._set_soup(soup)
        self._populate_room_information()

    def get_room_races(self) -> List[Race.Race]:
        return self._room_races

    def _is_destroyed(self) -> bool:
        return self._destroyed

    def _get_soup(self):
        return self._soup

    def _set_destroyed(self, destroyed: bool):
        self._destroyed = destroyed

    def _set_soup(self, soup: bs4.BeautifulSoup):
        print(type(soup))
        self._soup = soup
        self._set_destroyed(False)

    def _set_room_races(self, room_races: List[Race.Race]):
        self._room_races = room_races

    def _populate_room_information(self):
        if self._is_destroyed():
            raise Exception("This function is a private function and should only be called once internally.")
        try:
            all_ids = self._get_soup().find_all(id=True)[1:]
            for id_element in all_ids:
                self._add_front_room(id_element)

            # for front_room in self.get_front_room_races():
            #    print(f"{front_room.self_str()}\n\n\n")
        finally:
            self._get_soup().decompose()
            self._set_destroyed(True)

    def getRacesList(self, room_soup: Tag, mii_dict=None) -> List[Race.Race]:
        #Utility function
        table_rows = room_soup.find_all("tr")
        
        foundRaceHeader = False
        races = []
        for row in table_rows:
            if foundRaceHeader:
                foundRaceHeader = False
            else:
                if (row.get('id') is not None): #Found Race Header
                    #_ used to be the racenumber, but mkwx deletes races 24 hours after being played. This leads to rooms getting races removed, and even though
                    #they have race numbers, the number doesn't match where they actually are on the page
                    #This was leading to out of bounds exceptions.
                    raceTime, matchID, mkwxRaceNumber, roomID, roomType, cc, track, placements, is_ct = self.getRaceInfoFromList(row.findAll(text=True))
                    room_rxx = self._get_rxx_from_line(row)
                    race_id = self._get_race_id_from_line(row)
                    trackURL = self._get_track_URL_from_line(row)
                    raceNumber = None
                    races.insert(0, Race.Race(raceTime, matchID, raceNumber, roomID, roomType, cc, track, is_ct, mkwxRaceNumber, room_rxx, race_id, trackURL))
                    foundRaceHeader = True
                    
                else:
                    FC, playerPageLink, ol_status, roomPosition, playerRegion, playerConnFails, role, vr, character_vehicle, delta, time, playerName = self.get_placement_info(row)
                    if races[0].hasFC(FC):
                        FC = FC + "-2"
                    mii_hex = None
                    if mii_dict is not None and FC in mii_dict:
                        mii_hex = mii_dict[FC].mii_data_hex_str
                    plyr = Player.Player(FC, playerPageLink, ol_status, roomPosition, playerRegion, playerConnFails, role, vr, character_vehicle, playerName, mii_hex=mii_hex)
                    p = Placement.Placement(plyr, -1, time, delta)
                    races[0].addPlacement(p)
        

            
        for race in races:
            if RoomPageParser.DEBUG_RACES:
                print()
                print(f"Room ID: {race.roomID}")
                print(f"Room rxx: {race.rxx}")
                print(f"Room Type: {race.roomType}")
                print(f"Race Match ID: {race.matchID}")
                print(f"Race ID: {race.raceID}")
                print(f"Race Time: {race.matchTime}")
                print(f"Race Number: {race.raceNumber}")
                print(f"Race Track: {race.track}")
                print(f"Track URL: {race.trackURL}")
                print(f"Race cc: {race.cc}")
                print(f"Is CT? {race.is_ct}")
            if RoomPageParser.DEBUG_PLACEMENTS:
                for placement in race.getPlacements():
                    print()
                    print(f"\tPlayer Name: {placement.getPlayer().name}")
                    print(f"\tPlayer FC: {placement.getPlayer().FC}")
                    print(f"\tPlayer Page: {placement.getPlayer().playerPageLink}")
                    print(f"\tPlayer ID: {placement.getPlayer().pid}")
                    print(f"\tFinish Time: {placement.get_time_string()}")
                    print(f"\tPlace: {placement.place}")
                    print(f"\tol_status: {placement.getPlayer().ol_status}")
                    print(f"\tPosition in Room: {placement.getPlayer().positionInRoom}")
                    print(f"\tPlayer Region: {placement.getPlayer().region}")
                    print(f"\tPlayer Conn Fails: {placement.getPlayer().playerConnFails}")
                    print(f"\tRole: {placement.getPlayer().role}")
                    print(f"\tVR: {placement.getPlayer().vr}")
                    print(f"\tCharacter: {placement.getPlayer().character}")
                    print(f"\tVehicle: {placement.getPlayer().vehicle}")
                    print(f"\tDiscord name: {placement.getPlayer().discord_name}")
                    print(f"\tLounge name: {placement.getPlayer().lounge_name}")
                    print(f"\tCharacter: {placement.getPlayer().character}")
                    print(f"\tVehicle: {placement.getPlayer().vehicle}")
                    print(f"\tPlayer Discord name: {placement.getPlayer().discord_name}")
                    print(f"\tPlayer lounge name: {placement.getPlayer().lounge_name}")
                    print(f"\tPlayer mii hex: {placement.getPlayer().mii_hex}")

        #We have a memory leak, and it's not incredibly clear how BS4 objects work and if
        #Python's automatic garbage collection can figure out how to collect
        while len(table_rows) > 0:
            del table_rows[0]
        

        #TODO: Could this be a bug now that rxx's can merge with themselves?
        seen_race_id_numbering = defaultdict(lambda:[{}, 0])
        for race in races:
            race:Race.Race
            rxx_numbering = seen_race_id_numbering[race.get_rxx()]
            if race.get_race_id() not in rxx_numbering:
                rxx_numbering[1] += 1
                rxx_numbering[0][race.get_race_id()] = rxx_numbering[1]
            race.set_race_number(rxx_numbering[0][race.get_race_id()])
        
        return races

    # ============= SOUP LEVEL FUNCTIONS =================
    @staticmethod
    def get_placement_info(bs4_tag: Tag):
        allRows = bs4_tag.find_all("td")
        playerPageLink = str(allRows[0].find("a")[common.HREF_HTML_NAME])
        
        
        FC = str(allRows[0].find("span").string)
        ol_status = str(allRows[1][common.TOOLTIP_NAME]).split(":")[1].strip()
    
        roomPosition = -1
        
        role = "-1"
        if (allRows[1].find("b") is not None):
            roomPosition = 1
            role = "host"
        else:
            temp = str(allRows[1].string).strip().split()
            roomPosition = temp[0].strip(".")
            role = temp[1].strip()
        
        playerRegion = str(allRows[2].string)
        playerConnFails = str(allRows[3].string)
        if not UtilityFunctions.isint(playerConnFails) and not UtilityFunctions.isfloat(playerConnFails):
            playerConnFails = None
        else:
            playerConnFails = float(playerConnFails)
        #TODO: Handle VR?
        vr = str(allRows[4].string)
        if not UtilityFunctions.isint(vr):
            vr = None
        else:
            vr = int(vr)
        
        character_vehicle = None
        if allRows[5].has_attr(common.TOOLTIP_NAME):
            character_vehicle = str(allRows[5][common.TOOLTIP_NAME])
        
        
        delta = str(allRows[7].string) # Not true delta, but significant delta (above .5)
        
        time = str(allRows[8].string)
        
        playerName = str(allRows[9].string)
        while len(allRows) > 0:
            del allRows[0]
        
        return FC, playerPageLink, ol_status, roomPosition, playerRegion, playerConnFails, role, vr, character_vehicle, delta, time, playerName
    
    def getRaceInfoFromList(self, textList):
        '''Utility Function'''
        raceTime = str(textList[0])
        UTCIndex = raceTime.index("UTC")
        raceTime = raceTime[:UTCIndex+3]
        
        matchID = str(textList[1])
        
        raceNumber = str(textList[2]).strip().strip("(").strip(")").strip("#")
        
        roomID = str(textList[4])
        
        roomType = str(textList[6])
        
        cc = str(textList[7])[3:-2] #strip white spaces, the star, and the cc
        is_ct = str(textList[-1]) in {'u', 'c'}
        track = "Unknown_Track (Bad HTML, mkwx messed up)"
        try:
            if len(textList) == 12:
                track = str(textList[9])
            elif len(textList) == 10:
                track = str(textList[8]).split(":")[-1].strip()
            else:
                track = str(textList[9]).strip()
        except IndexError:
            pass
        
        placements = []
        
        while len(textList) > 0:
            del textList[0]
        
        return raceTime, matchID, raceNumber, roomID, roomType, cc, track, placements, is_ct
    
    def _get_rxx_from_line(self, html_line: Tag) -> str:
        roomLink = html_line.find_all('a')[1][common.HREF_HTML_NAME]
        return roomLink.split("/")[-1]
        
    def _get_race_id_from_line(self, html_line):
        return html_line.get('id')
    
    def _get_track_URL_from_line(self, html_line):
        try:
            return html_line.find_all('a')[2][common.HREF_HTML_NAME]
        except IndexError:
            return "No Track Page"
    

class FrontPageParser(object):
    '''
    classdocs
    '''
    def __init__(self, soup):
        self._set_front_room_races(list())
        self._set_soup(soup)
        self._populate_rooms_information()

    def get_front_room_races(self) -> List[Race.Race]:
        return self._front_room_races

    def _is_destroyed(self) -> bool:
        return self._destroyed

    def _get_soup(self):
        return self._soup

    def _set_destroyed(self, destroyed: bool):
        self._destroyed = destroyed

    def _set_soup(self, soup: bs4.BeautifulSoup):
        print(type(soup))
        self._soup = soup
        self._set_destroyed(False)

    def _set_front_room_races(self, front_room_races: List[Race.Race]):
        self._front_room_races = front_room_races



    @staticmethod
    def parse_front_room_into_placements(bs4_racer_tag: Tag):
        placements = []
        number_of_players = 1
        try:
            all_rows = bs4_racer_tag.find_all("td")
            if len(all_rows) != 11:
                print("Not 11...")
                [print(row, "\n----------------") for row in all_rows]
                return []
            
            has_guest_player = len([c for c in all_rows[9].children]) == 3
            
            if has_guest_player:
                number_of_players = 2
                FCs = []
                FCs.append(str(all_rows[0].find("a").string))
                FCs.append(f"{FCs[0]}-guest")
                playerPageLink = str(all_rows[0].find("a")[common.HREF_HTML_NAME])
                ol_status = ""

                roomPosition, role = ''.join(all_rows[1].findAll(text=True)).strip('\u2007').split('.')
                roomPosition = roomPosition.strip()
                if not roomPosition.isnumeric():
                    roomPosition = -1
                else:
                    roomPosition = int(roomPosition)
                role = role.strip().lower()
                
                roomPositions = [roomPosition, roomPosition]
                roles = [role, role]
                
                region = all_rows[3].string.strip()
                regions = [region, region]
                
                vrs = [all_rows[5].string.strip(), 5000]
                
                
                vehicle_combinations = [None, None]
                if all_rows[6].has_attr(common.TOOLTIP_NAME):
                    vehicle_combination = all_rows[6][common.TOOLTIP_NAME]
                    if '<br>' in vehicle_combination:
                        combo1, combo2 = vehicle_combination.split('<br>')
                        vehicle_combinations = [combo1, combo2]
                    else:
                        vehicle_combinations = [vehicle_combination, vehicle_combination]
                
                
                times = [time for time in all_rows[9].findAll(text=True)]
                
                playerNames = [name for name in all_rows[10].findAll(text=True)]
                if len(playerNames) < 2:
                    playerNames.append('no name')
                    playerNames.append('no name')
                index = 0
                plyr1 = Player.Player(FC=FCs[index], playerPageLink=playerPageLink, ol_status=ol_status, roomPosition=roomPositions[index], playerRegion=regions[index], playerConnFails=None, role=roles[index], vr=vrs[index], character_vehicle=vehicle_combinations[index], playerName=playerNames[index])
                index = 1
                plyr2 = Player.Player(FC=FCs[index], playerPageLink=playerPageLink, ol_status=ol_status, roomPosition=roomPositions[index], playerRegion=regions[index], playerConnFails=None, role=roles[index], vr=vrs[index], character_vehicle=vehicle_combinations[index], playerName=playerNames[index])
                
                placements.append(Placement.Placement(plyr1, -1, times[0]))
                placements.append(Placement.Placement(plyr2, -1, times[1]))
                
            else:            
                
            
                FC = str(all_rows[0].find("a").string)
                playerPageLink = str(all_rows[0].find("a")[common.HREF_HTML_NAME])
                ol_status = ""
                
                roomPosition, role = ''.join(all_rows[1].findAll(text=True)).strip('\u2007').split('.')
                roomPosition = roomPosition.strip()
                role = role.strip().lower()
                    
                region = all_rows[3].string.strip()
                
                
                #TODO: Handle VR?
                vr = all_rows[5].string.strip()
                
                vehicle_combination = None
                if 'title' in all_rows[6].attrs:
                    vehicle_combination = all_rows[6]['title']
                    
                
                #roomType is 4
                
                time = str(all_rows[9].string)
                
                playerName = str(all_rows[10].string)
                
                
                while len(all_rows) > 0:
                    del all_rows[0]
                    
                plyr = Player.Player(FC=FC, playerPageLink=playerPageLink, ol_status=ol_status, roomPosition=roomPosition, playerRegion=region, playerConnFails=None, role=role, vr=vr, character_vehicle=vehicle_combination, playerName=playerName)
                p = Placement.Placement(plyr, -1, time)
                placements.append(p)
        except Exception as e:
            print(e)
            raise
        return number_of_players, placements

    @staticmethod
    def parse_front_room_into_race(bs4_room_header: Tag) -> Race:
        print(bs4_room_header)
        rxx = str(bs4_room_header["id"])
        roomInfo = bs4_room_header.find("th").findAll(text=True)
        matchID = None
        matchTime = None
        roomType = None
        raceNumber = None
        roomID = None
        cc = None
        track = None
        print(roomInfo[-1])
        is_ct = roomInfo[-1] != 'n'
        if len(roomInfo) == 12:
            matchID = None
            matchTime = roomInfo[5]
            roomType = roomInfo[3]
            raceNumber = roomInfo[5]
            roomID = roomInfo[1]
            cc = roomInfo[4]
            track = roomInfo[9]
        elif len(roomInfo) == 11:
            matchID = None
            matchTime = roomInfo[5]
            roomType = roomInfo[3]
            raceNumber = roomInfo[5]
            roomID = roomInfo[1]
            cc = roomInfo[4]
            track = roomInfo[8]
        elif len(roomInfo) == 8:
            matchID = None
            matchTime = roomInfo[5]
            roomType = roomInfo[3]
            raceNumber = roomInfo[5]
            roomID = roomInfo[1]
            cc = roomInfo[4]
            track = None
        elif len(roomInfo) == 7:
            matchID = None
            roomID = roomInfo[1]
            roomType = roomInfo[3]
            track = None
            if roomInfo[4].endswith('0cc') or roomInfo[4].endswith('Mirror'):
                cc = roomInfo[4]
                raceNumber = roomInfo[5]
                matchTime = roomInfo[5]
            else:
                cc = None
                raceNumber = None
                matchTime = None
        elif len(roomInfo) == 6:
            matchID = None
            matchTime = None
            roomType = roomInfo[3]
            raceNumber = None
            roomID = roomInfo[1]
            cc = None
            track = None
        elif len(roomInfo) == 9:
            matchID = None
            roomID = roomInfo[1]
            roomType = roomInfo[3]
            cc = roomInfo[4]
            raceNumber = roomInfo[5]
            matchTime = roomInfo[5]
            track = roomInfo[7]
        elif len(roomInfo) == 10:
            matchID = None
            roomID = roomInfo[1]
            roomType = roomInfo[3]
            cc = roomInfo[4]
            if roomInfo[5].strip() != "":
                raceNumber = roomInfo[5]
                matchTime = roomInfo[5]
                track = roomInfo[8]
            else:
                raceNumber = None
                matchTime = None
                track = roomInfo[7]
        else:
            print(len(roomInfo))
            print(roomInfo)
            print(f"RoomID: {roomID}, roomType: {roomType}, cc: {cc}, matchTime: {matchTime}, raceNumber: {raceNumber}, track: {track}")

            
        if cc is not None:
            cc = cc[3:].strip()
        if matchTime is not None:
            if '(' in matchTime and ')' in matchTime:
                matchTime = matchTime[matchTime.index('(')+1:matchTime.index(')')]
            if '(' in raceNumber:
                raceNumber = raceNumber[:raceNumber.index('(')].strip()
        if raceNumber is not None:
            raceNumber = raceNumber.strip()
            if raceNumber.startswith("Match #"):
                raceNumber = raceNumber[len("Match #"):]
            if UtilityFunctions.isint(raceNumber):
                raceNumber = int(raceNumber)
            else:
                raceNumber = None
        if track is not None:
            track = track.replace('Last track:', '').strip()
        #print(f"RoomID: {roomID}, roomType: {roomType}, cc: {cc}, matchTime: {matchTime}, raceNumber: {raceNumber}, track: {track}")
                
        return Race.Race(matchTime, matchID, raceNumber, roomID, roomType, cc, track, is_ct=is_ct, mkwxRaceNumber=raceNumber, rxx=rxx)

    
        
    def _add_front_room(self, bs4_front_room_header):
        if bs4_front_room_header is None:
            return
        front_room_race = FrontPageParser.parse_front_room_into_race(bs4_front_room_header)
        if front_room_race is None:
            return
        
        
        #2 because the first element is an empty navigable string and the 2nd is the garbage info
        total_players = 0
        for element in itertools.islice(bs4_front_room_header.next_siblings, 2, None):
            if element is None:
                print("element was None")
                return
            if isinstance(element, NavigableString):
                continue
            if 'id' in element.attrs:
                break
            
            #Can be more than one placement if the line contains a guest as well
            num_players, placements = FrontPageParser.parse_front_room_into_placements(element)
            for placement in placements:
                front_room_race.placements.append(placement)
            total_players += num_players
            if total_players != len(front_room_race.placements):
                print(total_players, len(front_room_race.placements))
                print("Mismatch of placements and number of players, check code for bugs. Line #253 in SimpleRooms.py")
        front_room_race.update_region()
        self.get_front_room_races().append(front_room_race)

    def _populate_rooms_information(self):
        if self._is_destroyed():
            raise Exception("This function is a private function and should only be called once internally.")
        try:
            all_ids = self._get_soup().find_all(id=True)[1:]
            for id_element in all_ids:
                self._add_front_room(id_element)

            # for front_room in self.get_front_room_races():
            #    print(f"{front_room.self_str()}\n\n\n")
        finally:
            self._get_soup().decompose()
            self._set_destroyed(True)
        
    def get_CTGP_WWs(self):
        return sorted([room for room in self.get_front_room_races() if room.isCTGPWW()], key=lambda r:r.getRoomRating(), reverse=True)
    
    def get_RT_WWs(self):
        return sorted([room for room in self.get_front_room_races() if room.isRTWW()], key=lambda r:r.getRoomRating(), reverse=True)
    
    def get_battle_WWs(self):
        return sorted([room for room in self.get_front_room_races() if room.isBattleWW()], key=lambda r:r.getRoomRating(), reverse=True)
    
    def get_private_rooms(self):
        return sorted([room for room in self.get_front_room_races() if room.isPrivateRoom()], key=lambda r:r.getRoomRating(), reverse=True)
    
    def get_other_rooms(self):
        return sorted([room for room in self.get_front_room_races() if room.isUnknownRegion()], key=lambda r:r.getRoomRating(), reverse=True)
    
    @staticmethod
    def get_embed_text_for_race(races:List[Race.Race], pageNumber):
        if len(races) == 0:
            return "No rooms"
        if pageNumber < 0:
            pageNumber = 0
        if pageNumber > len(races):
            pageNumber = len(races) - 1
        
        race = races[pageNumber]
        cur_track = race.getTrackNameWithoutAuthor()
        spots_available = 12 - len(race.placements)
        if spots_available == 0:
            spots_string = "Full Room"
        else:
            spots_string = f"{spots_available} Free Spot{'s' if spots_available > 1 else ''}"

        room_str = f"+ {race.getWWFullName(race.region)} Room Rating (out of 100): {race.getRoomRating()}\n\n" \
                   f"- Room {race.roomID} - {cur_track} ({race.matchTime}) - {spots_string}"
        
            
        str_msg =  "```diff\n" + str(room_str).strip() + "\n\n"
        vr_br_str_full = 'Battle Rating' if race.isBattleWW() else "Versus Rating"
        str_msg += '+{:>3} {:<13}| {:<13}| {:<15}| {:<1}\n'.format("#.", "Lounge Name", "Mii Name", "FC", vr_br_str_full) 
        
        for placement in race.placements:
            lounge_name = UserDataProcessing.lounge_get(placement.player.FC)
            roomPosition = placement.player.positionInRoom
            FC = placement.player.FC
            mii_name = placement.player.name
            vr = placement.player.vr
            if lounge_name == "":
                lounge_name = "UNKNOWN"
            vr_br_str = ' BR' if race.isBattleWW() else " VR"
            str_msg += "{:>4} {:<13}| {:<13}| {:<15}| {:<1}\n".format(str(roomPosition)+".",lounge_name, mii_name, FC, str(vr)+vr_br_str)
        
        str_msg += f"\nPage {pageNumber+1}/{len(races)}```"
        return str_msg
    
    
        
        