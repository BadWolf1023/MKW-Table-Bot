'''
Created on May 6, 2021

@author: willg
'''
    
import WiimmfiSiteFunctions
import Player
import Placement
import Race
import UserDataProcessing
from bs4 import NavigableString
from bs4.element import Tag
import itertools
import asyncio
from typing import List


def get_placements_from_mkwx_bs4_tag(bs4_racer_tag:Tag):
    placements = []
    number_of_players = 1
    try:
        allRows = bs4_racer_tag.find_all("td")
        if len(allRows) != 11:
            print("Not 11...")
            [print(row, "\n----------------") for row in allRows]
            return []
        
        has_guest_player = len([c for c in allRows[9].children]) == 3
        
        if has_guest_player:
            number_of_players = 2
            FCs = []
            FCs.append(str(allRows[0].find("a").string))
            FCs.append(f"{FCs[0]}-guest")
            
            
            roomPosition, role = ''.join(allRows[1].findAll(text=True)).strip('\u2007').split('.')
            roomPosition = roomPosition.strip()
            if not roomPosition.isnumeric():
                roomPosition = -1
            else:
                roomPosition = int(roomPosition)
            role = role.strip().lower()
            
            roomPositions = [roomPosition, roomPosition]
            roles = [role, role]
            
            room_type = allRows[3].string.strip()
            room_types = [room_type, room_type]
            
            vrs = [allRows[5].string.strip(), 5000]
            
            
            vehicle_combinations = [None, None]
            if 'data-tooltip' in allRows[6].attrs:
                vehicle_combination = allRows[6]['data-tooltip']
                if '<br>' in vehicle_combination:
                    combo1, combo2 = vehicle_combination.split('<br>')
                    vehicle_combinations = [combo1, combo2]
                else:
                    vehicle_combinations = [vehicle_combination, vehicle_combination]
            
            
            times = [time for time in allRows[9].findAll(text=True)]
            
            playerNames = [name for name in allRows[10].findAll(text=True)]
            if len(playerNames) < 2:
                playerNames.append('no name')
                playerNames.append('no name')
            index = 0
            plyr1 = Player.Player(FCs[index], playerNames[index], roles[index], roomPositions[index], vrs[index], driver_vehicle=vehicle_combinations[index], room_type=room_types[index])
            index = 1
            plyr2 = Player.Player(FCs[index], playerNames[index], roles[index], roomPositions[index], vrs[index], driver_vehicle=vehicle_combinations[index], room_type=room_types[index])
            
            placements.append(Placement.Placement(plyr1, -1, times[0]))
            placements.append(Placement.Placement(plyr2, -1, times[1]))
            
        else:            
            
        
            FC = str(allRows[0].find("a").string)
            
            
            roomPosition, role = ''.join(allRows[1].findAll(text=True)).strip('\u2007').split('.')
            roomPosition = roomPosition.strip()
            role = role.strip().lower()
                
            room_type = allRows[3].string.strip()
            
            
            #TODO: Handle VR?
            vr = allRows[5].string.strip()
            
            vehicle_combination = None
            if 'title' in allRows[6].attrs:
                vehicle_combination = allRows[6]['title']
                
            
            #roomType is 4
            
            time = str(allRows[9].string)
            
            playerName = str(allRows[10].string)
            
            
            while len(allRows) > 0:
                del allRows[0]
            
            
            
            plyr = Player.Player(FC, playerName, role, roomPosition, vr, driver_vehicle=vehicle_combination, room_type=room_type)
            p = Placement.Placement(plyr, -1, time)
            placements.append(p)
    except Exception as e:
        print(e)
        raise
    return number_of_players, placements


def get_race_from_mkwx_bs4_room_header(bs4_room_header:List[str]):
    roomInfo = bs4_room_header.find("th").findAll(text=True)
    matchID = None
    matchTime = None
    roomType = None
    raceNumber = None
    roomID = None
    cc = None
    track = None
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
    if track is not None:
        track = track.replace('Last track:', '').strip()
    #print(f"RoomID: {roomID}, roomType: {roomType}, cc: {cc}, matchTime: {matchTime}, raceNumber: {raceNumber}, track: {track}")
            
    return Race.Race(matchTime, matchID, raceNumber, roomID, roomType, cc, track)

    


class SimpleRooms(object):
    '''
    classdocs
    '''
    def __init__(self):
        self.rooms = []
        
    def add_room_data(self, bs4_room_header):
        if bs4_room_header is None:
            return
        cur_room = get_race_from_mkwx_bs4_room_header(bs4_room_header)
        if cur_room is None:
            return
        
        
        #2 because the first element is an empty navigable string and the 2nd is the garbage info
        total_players = 0
        for element in itertools.islice(bs4_room_header.next_siblings, 2, None):
            if element is None:
                print("element was None")
                return
            if isinstance(element, NavigableString):
                continue
            if 'id' in element.attrs:
                break
            """
            print(element)
            print("=========================")"""
            
            #Can be more than one placement if the line contains a guest as well
            num_players, placements = get_placements_from_mkwx_bs4_tag(element)
            for placement in placements:
                cur_room.placements.append(placement)
            total_players += num_players
            if total_players != len(cur_room.placements):
                print(total_players, len(cur_room.placements))
                print("Mismatch of placements and number of players, check code for bugs. Line #258 in SimpleRooms.py")
        cur_room.setRegionFromPlacements()
        self.rooms.append(cur_room)

            
        
    #getRoomLinkByFC old name
    async def populate_rooms_information(self):
        soup = await WiimmfiSiteFunctions.getMKWXSoup()
        all_ids = soup.find_all(id=True)[1:]
        for id_element in all_ids:
            self.add_room_data(id_element)
            
    def get_CTGP_WWs(self):
        return sorted([room for room in self.rooms if room.isCTGPWW()], key=lambda r:r.getRoomRating(), reverse=True)
    
    def get_RT_WWs(self):
        return sorted([room for room in self.rooms if room.isRTWW()], key=lambda r:r.getRoomRating(), reverse=True)
    
    def get_battle_WWs(self):
        return sorted([room for room in self.rooms if room.isBattleWW()], key=lambda r:r.getRoomRating(), reverse=True)
    
    def get_private_rooms(self):
        return sorted([room for room in self.rooms if room.isPrivateRoom()], key=lambda r:r.getRoomRating(), reverse=True)
    
    def get_other_rooms(self):
        return sorted([room for room in self.rooms if room.isUnknownRoomType()], key=lambda r:r.getRoomRating(), reverse=True)
    
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
        room_str = f"+ {race.getWWFullName(race.region)} Room Rating (out of 100): {race.getRoomRating()}\n\n- Room {race.roomID} - {cur_track} ({race.matchTime}) -"
        
        #if len(last_match) == 0:
        #    room_str += "Not started"
        #else:
        #    room_str += last_match
            
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
    
    
    
        
if __name__ == '__main__':
    sr = SimpleRooms()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(sr.populate_rooms_information())
    
    ctgp_wws = sr.get_CTGP_WWs()
    for ctgp_ww in ctgp_wws:
        print(ctgp_ww.roomID, ctgp_ww.getRoomRating())
    print(SimpleRooms.get_embed_text_for_race(ctgp_wws, 0)[1])
        
        