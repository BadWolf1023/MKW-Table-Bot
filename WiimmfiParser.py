'''
Created on May 6, 2021

@author: willg
'''

import itertools
from typing import List, Tuple
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

    def has_races(self) -> bool:
        return isinstance(self.get_room_races(), list) and len(self.get_room_races()) > 0

    def _is_destroyed(self) -> bool:
        return self._destroyed

    def _get_soup(self):
        return self._soup

    def _set_destroyed(self, destroyed: bool):
        self._destroyed = destroyed

    def _set_soup(self, soup: bs4.BeautifulSoup):
        self._soup = soup
        self._set_destroyed(False)

    def _set_room_races(self, room_races: List[Race.Race]):
        self._room_races = room_races

    def _populate_room_information(self):
        if self._is_destroyed():
            raise Exception(
                "This function is a private function and should only be called once internally.")
        try:
            self._set_room_races(self._get_races_list())
        finally:
            self._get_soup().decompose()
            self._set_destroyed(True)

    def _get_races_list(self, mii_dict=None) -> List[Race.Race]:
        room_soup = self._get_soup()
        table_rows = room_soup.find_all("tr")

        foundRaceHeader = False
        races = []
        for row in table_rows:
            if foundRaceHeader:
                foundRaceHeader = False
            else:
                if (row.get('id') is not None):  # Found Race Header
                    # _ used to be the racenumber, but mkwx deletes races 24 hours after being played. This leads to rooms getting races removed, and even though
                    # they have race numbers, the number doesn't match where they actually are on the page
                    # This was leading to out of bounds exceptions.
                    raceTime, matchID, mkwxRaceNumber, roomID, roomType, cc, track, placements, is_ct = RoomPageParser._get_race_data(
                        row.findAll(text=True))
                    room_rxx = RoomPageParser._get_rxx_from_line(row)
                    race_id = RoomPageParser._get_race_id_from_line(row)
                    trackURL = RoomPageParser._get_track_URL_from_line(row)
                    raceNumber = None
                    races.insert(0, Race.Race(raceTime, matchID, raceNumber, roomID, roomType,
                                 cc, track, is_ct, mkwxRaceNumber, room_rxx, race_id, trackURL))
                    foundRaceHeader = True

                else:  # It is a player row (since it is not the race header)
                    FC, player_url, ol_status, roomPosition, playerRegion, playerConnFails, role, vr, character_vehicle, delta, time, playerName = RoomPageParser._get_placement_info(
                        row)
                    if races[0].hasFC(FC):
                        FC = FC + "-2"
                    mii_hex = None
                    if mii_dict is not None and FC in mii_dict:
                        mii_hex = mii_dict[FC].mii_data_hex_str
                    plyr = Player.Player(FC, player_url, ol_status, roomPosition, playerRegion,
                                         playerConnFails, role, vr, character_vehicle, playerName, mii_hex=mii_hex)
                    p = Placement.Placement(plyr, time, delta)
                    races[0].addPlacement(p)

        for race in races:
            if RoomPageParser.DEBUG_RACES:
                print()
                print(f"Room ID: {race.get_room_name()}")
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
                    print(f"\tPlayer Name: {placement.get_player().get_mii_name()}")
                    print(f"\tPlayer FC: {placement.get_player().get_FC()}")
                    print(
                        f"\tPlayer Page: {placement.get_player().get_url()}")
                    print(f"\tPlayer ID: {placement.get_player().get_player_id()}")
                    print(f"\tFinish Time: {placement.get_time_string()}")
                    print(f"\tPlace: {placement.get_place()}")
                    print(f"\tol_status: {placement.get_player().get_ol_status()}")
                    print(
                        f"\tPosition in Room: {placement.get_player().get_room_position()}")
                    print(f"\tPlayer Region: {placement.get_player().get_region()}")
                    print(
                        f"\tPlayer Conn Fails: {placement.get_player().get_connection_fails()}")
                    print(f"\tRole: {placement.get_player().get_role()}")
                    print(f"\tVR: {placement.get_player().get_versus_rating()}")
                    print(f"\tCharacter: {placement.get_player().get_character()}")
                    print(f"\tVehicle: {placement.get_player().get_vehicle()}")
                    print(
                        f"\tDiscord name: {placement.get_player().get_discord_name()}")
                    print(
                        f"\tLounge name: {placement.get_player().get_lounge_name()}")
                    print(f"\tCharacter: {placement.get_player().get_character()}")
                    print(f"\tVehicle: {placement.get_player().get_vehicle()}")
                    print(
                        f"\tPlayer Discord name: {placement.get_player().get_discord_name()}")
                    print(
                        f"\tPlayer lounge name: {placement.get_player().get_lounge_name()}")
                    print(f"\tPlayer mii hex: {placement.get_player().get_mii_hex()}")

        # We have a memory leak, and it's not incredibly clear how BS4 objects work and if
        # Python's automatic garbage collection can figure out how to collect
        while len(table_rows) > 0:
            del table_rows[0]

        for race_num, race in enumerate(races, 1):
            race.set_race_number(race_num)

        return races

    # ============= SOUP LEVEL FUNCTIONS =================
    @staticmethod
    def _get_placement_info(bs4_tag: Tag):
        all_rows = bs4_tag.find_all("td")
        player_url = str(all_rows[0].find("a")[common.HREF_HTML_NAME])

        FC = str(all_rows[0].find("span").string)
        ol_status = str(all_rows[1][common.TOOLTIP_NAME]).split(":")[1].strip()

        room_position = -1

        role = "Unknown"
        if (all_rows[1].find("b") is not None):
            room_position = 1
            role = "host"
        else:
            temp = str(all_rows[1].string).strip().split()
            room_position = temp[0].strip(".")
            room_position = int(room_position) if UtilityFunctions.is_int(room_position) else -1
            role = temp[1].strip()

        player_region = str(all_rows[2].string)
        player_conn_fails = str(all_rows[3].string)
        if UtilityFunctions.is_int(player_conn_fails) or UtilityFunctions.is_float(player_conn_fails):
            player_conn_fails = float(player_conn_fails)
        else:
            player_conn_fails = 0.0
        # TODO: Handle VR?
        vr = str(all_rows[4].string)
        vr = int(vr) if UtilityFunctions.is_int(vr) else None

        character_vehicle = None
        if all_rows[5].has_attr(common.TOOLTIP_NAME):
            character_vehicle = str(all_rows[5][common.TOOLTIP_NAME])

        # Not true delta, but significant delta (above .5)
        delta = str(all_rows[7].string)
        delta = float(delta) if UtilityFunctions.is_float(delta) else None
        time = str(all_rows[8].string)
        player_name = str(all_rows[9].string)
        while len(all_rows) > 0:
            del all_rows[0]

        return FC, player_url, ol_status, room_position, player_region, player_conn_fails, role, vr, character_vehicle, delta, time, player_name

    @staticmethod
    def _get_race_data(text_list) -> Tuple[str, str, str, str, str, str, str, List, bool]:
        '''Utility Function'''
        race_start_time = str(text_list[0])
        UTC_index = race_start_time.index("UTC")
        race_start_time = race_start_time[:UTC_index+3]
        match_id = str(text_list[1])
        race_number = str(text_list[2]).strip().strip(
            "(").strip(")").strip("#")
        room_id = str(text_list[4])
        room_type = str(text_list[6])
        # strip white spaces, the star, and the cc
        cc = str(text_list[7])[3:-2]
        is_ct = str(text_list[-1]) in {'u', 'c'}
        placements = []
        track_name = "Unknown_Track (Bad HTML, mkwx messed up)"
        try:
            if len(text_list) == 10:
                track_name = str(text_list[8]).split(":")[-1].strip()
            else:
                track_name = str(text_list[9]).strip()
        except IndexError:
            pass

        while len(text_list) > 0:
            del text_list[0]

        return race_start_time, match_id, race_number, room_id, room_type, cc, track_name, placements, is_ct

    @staticmethod
    def _get_rxx_from_line(html_line: Tag) -> str:
        room_link = html_line.find_all('a')[1][common.HREF_HTML_NAME]
        return room_link.split("/")[-1]

    @staticmethod
    def _get_race_id_from_line(html_line: Tag) -> str:
        return html_line.get('id')

    @staticmethod
    def _get_track_URL_from_line(html_line: Tag) -> str:
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
                player_url = str(all_rows[0].find("a")[
                    common.HREF_HTML_NAME])
                ol_status = ""

                room_position, role = ''.join(all_rows[1].findAll(
                    text=True)).strip('\u2007').split('.')
                room_position = room_position.strip()
                room_position = int(room_position) if UtilityFunctions.is_int(room_position) else -1
                role = role.strip().lower()

                roomPositions = [room_position, room_position]
                roles = [role, role]

                region = all_rows[3].string.strip()
                regions = [region, region]

                vrs = [all_rows[5].string.strip(), 5000]
                vrs[0] = int(vrs[0]) if UtilityFunctions.is_int(vrs[0]) else None

                vehicle_combinations = [None, None]
                if all_rows[6].has_attr(common.TOOLTIP_NAME):
                    vehicle_combination = all_rows[6][common.TOOLTIP_NAME]
                    if '<br>' in vehicle_combination:
                        combo1, combo2 = vehicle_combination.split('<br>')
                        vehicle_combinations = [combo1, combo2]
                    else:
                        vehicle_combinations = [
                            str(vehicle_combination), str(vehicle_combination)]

                times = [str(time) for time in all_rows[9].findAll(text=True)]

                playerNames = [str(name) for name in all_rows[10].findAll(text=True)]
                if len(playerNames) < 2:
                    playerNames.append('no name')
                    playerNames.append('no name')
                index = 0
                plyr1 = Player.Player(FC=FCs[index], player_url=player_url, ol_status=ol_status, room_position=roomPositions[index], region=regions[index],
                                      connection_fails=0.0, role=roles[index], vr=vrs[index], character_vehicle=vehicle_combinations[index], mii_name=playerNames[index])
                index = 1
                plyr2 = Player.Player(FC=FCs[index], player_url=player_url, ol_status=ol_status, room_position=roomPositions[index], region=regions[index],
                                      connection_fails=0.0, role=roles[index], vr=vrs[index], character_vehicle=vehicle_combinations[index], mii_name=playerNames[index])

                placements.append(Placement.Placement(plyr1, times[0]))
                placements.append(Placement.Placement(plyr2, times[1]))

            else:

                FC = str(all_rows[0].find("a").string)
                player_url = str(all_rows[0].find("a")[
                    common.HREF_HTML_NAME])
                ol_status = ""

                room_position, role = ''.join(all_rows[1].findAll(
                    text=True)).strip('\u2007').split('.')
                room_position = room_position.strip()
                room_position = int(room_position) if UtilityFunctions.is_int(room_position) else -1
                role = role.strip().lower()

                region = all_rows[3].string.strip()

                # TODO: Handle VR?
                vr = all_rows[5].string.strip()
                vr = int(vr) if UtilityFunctions.is_int(vr) else None

                vehicle_combination = None
                if 'title' in all_rows[6].attrs:
                    vehicle_combination = str(all_rows[6]['title'])

                #roomType is 4

                time = str(all_rows[9].string)

                playerName = str(all_rows[10].string)

                while len(all_rows) > 0:
                    del all_rows[0]

                plyr = Player.Player(FC=FC, player_url=player_url, ol_status=ol_status, room_position=room_position, region=region,
                                     connection_fails=0.0, role=role, vr=vr, character_vehicle=vehicle_combination, mii_name=playerName)
                p = Placement.Placement(plyr, time)
                placements.append(p)

        except Exception as e:
            print(e)
            raise
        return number_of_players, placements

    @staticmethod
    def parse_front_room_into_race(bs4_room_header: Tag) -> Race.Race:
        rxx = str(bs4_room_header["id"])
        room_info = bs4_room_header.find("th").findAll(text=True)
        match_id = None
        match_time = None
        room_type = None
        race_number = None
        room_id = None
        cc = None
        track = None
        is_ct = room_info[-1] != 'n'
        if len(room_info) == 12:
            match_id = None
            match_time = room_info[5]
            room_type = room_info[3]
            race_number = room_info[5]
            room_id = room_info[1]
            cc = room_info[4]
            track = room_info[9]
        elif len(room_info) == 11:
            match_id = None
            match_time = room_info[5]
            room_type = room_info[3]
            race_number = room_info[5]
            room_id = room_info[1]
            cc = room_info[4]
            track = room_info[8]
        elif len(room_info) == 8:
            match_id = None
            match_time = room_info[5]
            room_type = room_info[3]
            race_number = room_info[5]
            room_id = room_info[1]
            cc = room_info[4]
            track = None
        elif len(room_info) == 7:
            match_id = None
            room_id = room_info[1]
            room_type = room_info[3]
            track = None
            if room_info[4].endswith('0cc') or room_info[4].endswith('Mirror'):
                cc = room_info[4]
                race_number = room_info[5]
                match_time = room_info[5]
            else:
                cc = None
                race_number = None
                match_time = None
        elif len(room_info) == 6:
            match_id = None
            match_time = None
            room_type = room_info[3]
            race_number = None
            room_id = room_info[1]
            cc = None
            track = None
        elif len(room_info) == 9:
            match_id = None
            room_id = room_info[1]
            room_type = room_info[3]
            cc = room_info[4]
            race_number = room_info[5]
            match_time = room_info[5]
            track = room_info[7]
        elif len(room_info) == 10:
            match_id = None
            room_id = room_info[1]
            room_type = room_info[3]
            cc = room_info[4]
            if room_info[5].strip() != "":
                race_number = room_info[5]
                match_time = room_info[5]
                track = room_info[8]
            else:
                race_number = None
                match_time = None
                track = room_info[7]
        else:
            print(len(room_info))
            print(room_info)
            print(f"RoomID: {room_id}, roomType: {room_type}, cc: {cc}, matchTime: {match_time}, raceNumber: {race_number}, track: {track}")

        if cc is not None:
            cc = cc[3:].strip()
        if match_time is not None:
            if '(' in match_time and ')' in match_time:
                match_time = match_time[match_time.index(
                    '(')+1:match_time.index(')')]
            if '(' in race_number:
                race_number = race_number[:race_number.index('(')].strip()
        if race_number is not None:
            race_number = race_number.strip()
            if race_number.startswith("Match #"):
                race_number = race_number[len("Match #"):]
            if UtilityFunctions.is_int(race_number):
                race_number = int(race_number)
            else:
                race_number = None
        if track is not None:
            track = track.replace('Last track:', '').strip()
        #print(f"RoomID: {roomID}, roomType: {roomType}, cc: {cc}, matchTime: {matchTime}, raceNumber: {raceNumber}, track: {track}")

        return Race.Race(match_time, match_id, race_number, room_id, room_type, cc, track, is_ct=is_ct, mkwx_race_number=race_number, rxx=rxx)

    def _add_front_room(self, bs4_front_room_header):
        if bs4_front_room_header is None:
            return
        front_room_race = FrontPageParser.parse_front_room_into_race(
            bs4_front_room_header)
        if front_room_race is None:
            return

        # 2 because the first element is an empty navigable string and the 2nd is the garbage info
        total_players = 0
        for element in itertools.islice(bs4_front_room_header.next_siblings, 2, None):
            if element is None:
                print("element was None")
                return
            if isinstance(element, NavigableString):
                continue
            if 'id' in element.attrs:
                break

            # Can be more than one placement if the line contains a guest as well
            num_players, placements = FrontPageParser.parse_front_room_into_placements(
                element)
            for placement in placements:
                front_room_race.placements.append(placement)
            total_players += num_players
            if total_players != len(front_room_race.placements):
                print(total_players, len(front_room_race.placements))
                print(
                    "Mismatch of placements and number of players, check code for bugs. Line #253 in SimpleRooms.py")
        front_room_race.update_region()
        self.get_front_room_races().append(front_room_race)

    def _populate_rooms_information(self):
        if self._is_destroyed():
            raise Exception(
                "This function is a private function and should only be called once internally.")
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
        return sorted([room for room in self.get_front_room_races() if room.isCTGPWW()], key=lambda r: r.getRoomRating(), reverse=True)

    def get_RT_WWs(self):
        return sorted([room for room in self.get_front_room_races() if room.isRTWW()], key=lambda r: r.getRoomRating(), reverse=True)

    def get_battle_WWs(self):
        return sorted([room for room in self.get_front_room_races() if room.isBattleWW()], key=lambda r: r.getRoomRating(), reverse=True)

    def get_private_rooms(self):
        return sorted([room for room in self.get_front_room_races() if room.isPrivateRoom()], key=lambda r: r.getRoomRating(), reverse=True)

    def get_other_rooms(self):
        return sorted([room for room in self.get_front_room_races() if room.isUnknownRegion()], key=lambda r: r.getRoomRating(), reverse=True)

    @staticmethod
    def get_embed_text_for_race(races: List[Race.Race], pageNumber):
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
                   f"- Room {race.get_room_name()} - {cur_track} ({race.matchTime}) - {spots_string}"

        str_msg = "```diff\n" + str(room_str).strip() + "\n\n"
        vr_br_str_full = 'Battle Rating' if race.isBattleWW() else "Versus Rating"
        str_msg += '+{:>3} {:<13}| {:<13}| {:<15}| {:<1}\n'.format(
            "#.", "Lounge Name", "Mii Name", "FC", vr_br_str_full)

        for placement in race.placements:
            lounge_name = UserDataProcessing.lounge_get(placement.get_player().get_FC())
            roomPosition = placement.get_player().get_room_position()
            FC = placement.get_player().get_FC()
            mii_name = placement.get_player().get_mii_name()
            vr = placement.get_player().get_versus_rating()
            if lounge_name == "":
                lounge_name = "UNKNOWN"
            vr_br_str = ' BR' if race.isBattleWW() else " VR"
            str_msg += "{:>4} {:<13}| {:<13}| {:<15}| {:<1}\n".format(
                str(roomPosition)+".", lounge_name, mii_name, FC, str(vr)+vr_br_str)

        str_msg += f"\nPage {pageNumber+1}/{len(races)}```"
        return str_msg
