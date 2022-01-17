'''
Created on Jul 30, 2020

@author: willg
'''
import WiimmfiSiteFunctions
import Table
from datetime import datetime
import humanize
from bs4 import NavigableString, Tag
import common
from typing import Dict, Tuple, List, Any
import ServerFunctions
from data_tracking import DataTracker
import UtilityFunctions


lorenzi_style_key = "#style"
#The key and first item of the tuple are sent when the list of options is requested, the second value is the code Lorenzi's site uses
styles = {"1":("Default", "default style"),
          "2":("Dark Theme", "dark"),
          "3":("Color by Ranking", "rank"),
          "4":("Mario Kart Universal", "mku"),
          "5":("200 League", "200l"),
          "6":("America's Cup", "americas"),
          "7":("Euro League", "euro"),
          "8":("マリオカートチームリーグ戦", "japan"),
          "9":("Clan War League", "cwl"),
          "10":("Runners Assemble", "runners"),
          "11":("Mario Kart Worlds", "mkworlds")
          }



lorenzi_graph_key = "#graph"
#The key and first item of the tuple are sent when the list of options is requested, the second value is the code Lorenzi's site uses 
graphs = {"1":("None", "default graph"),
          "2":("Absolute", "abs"),
          "3":("Difference (Two Teams Only)", "diff")
          }



DEFAULT_DC_POINTS = 3

class ChannelBot(object):
    '''
    classdocs
    '''
    def __init__(self, server_id=None, channel_id=None):
        self.loungeFinishTime = None
        self.set_table(None)
        self.set_war(None)
        self.prev_command_sw = False
        self.manualWarSetUp = False
        self.last_used = datetime.now()
        self.lastWPTime = None
        self.roomLoadTime = None
        self.save_states = []
        self.state_pointer = -1
        self.should_send_mii_notification = True
        self.set_style_and_graph(server_id)
        self.set_dc_points(server_id)
        self.server_id = server_id
        self.channel_id = channel_id
        self.race_size = 4

    def is_table_loaded(self) -> bool:
        return self.get_table() is not None
        

    def get_race_size(self) -> int:
        return self.race_size

    def get_table(self) -> Table.Table:
        return self._table
    def set_war(self, war) -> None:
        self.war = war
    def get_war(self) -> Table.War:
        return self.war
    def get_prev_command_sw(self) -> bool:
        return self.prev_command_sw
    def get_manual_war_set_up(self) -> bool:
        return self.manualWarSetUp
    def get_last_used(self):
        return self.last_used
    def get_lounge_finish_time(self) -> datetime:
        return self.loungeFinishTime
    def get_last_wptime(self) -> datetime:
        return self.lastWPTime
    def get_room_load_time(self) -> datetime:
        return self.roomLoadTime
    def get_save_states(self) -> List[Tuple[str, Dict[str, Any]]]:
        return self.save_states

    def get_should_send_mii_notification(self) -> bool:
        return self.should_send_mii_notification
    def get_server_id(self): # TODO: Add type hinting for this - is server_id an int or a str?
        return self.server_id
    def get_channel_id(self): # TODO: Add type hinting for this - is channel_id an int or a str?
        return self.channel_id
    def get_graph(self): # TODO: Add type hinting for this - is graph an int or a str?
        return self.graph
    def get_style(self): # TODO: Add type hinting for this - is style an int or a str?
        return self.style
    def get_dc_points(self) -> int:
        return self.dc_points
    def set_table(self, table):
        self._table = table
        self.updateLoungeFinishTime()


    def get_room_started_message(self) -> str:
        started_war_str = "FFA started" if self.get_war().is_FFA() else "War started"
        if not self.get_war().should_show_large_time_errors():
            started_war_str += " (ignoring errors for large finish times)"
        started_war_str += f". {self.get_table().getRXXText()}"
        return started_war_str
        
    def set_race_size(self, new_race_size: int):
        self.race_size = new_race_size

    
    def set_style_and_graph(self, server_id):
        self.graph = ServerFunctions.get_server_graph(server_id)
        self.style = ServerFunctions.get_server_table_theme(server_id)
    
    def set_dc_points(self, server_id):
        #self.dc_points = ServerFunctions.get_dc_points(server_id)
        self.dc_points = DEFAULT_DC_POINTS
    
    def get_lorenzi_style_and_graph(self, prepend_newline=True):
        result = '\n' if prepend_newline else ''
        result += self.get_lorenzi_style_str() + "\n"
        result += self.get_lorenzi_graph_str()
        return result
    
    def get_lorenzi_style_str(self) -> str:
        if self.style not in styles:
            return f"{lorenzi_style_key} {styles['1'][1]}"
        else:
            return f"{lorenzi_style_key} {styles[self.style][1]}"
        
    def get_lorenzi_graph_str(self) -> str:
        if self.graph not in graphs:
            return f"{lorenzi_graph_key} {graphs['1'][1]}"
        else:
            return f"{lorenzi_graph_key} {graphs[self.graph][1]}"
    
    def set_style(self, new_style):
        if new_style not in styles:
            return False
        self.style = new_style
        return True
    
    def set_graph(self, new_graph):
        if new_graph not in graphs:
            return False
        self.graph = new_graph
        return True
    
    def get_style_name(self, style=None):
        if style is None:
            return styles[self.style][0]
        if style in styles:
            return styles[style][0]
        else:
            "Error"
            
                
    def get_graph_name(self, graph=None):
        if graph is None:
            return graphs[self.graph][0]
        if graph in graphs:
            return graphs[graph][0]
        else:
            "Error"
        
    
    def is_valid_style(self, style):
        return style in styles

    def is_valid_graph(self, graph):
        return graph in graphs
        
    #Caller must ensure the dict is in the format key=str, value=tuple(str, str)
    def __get_list_text__(self, dict_list:Dict[str, Tuple[str, str]]):
        final_text = ""
        for key, (display_text, _) in dict_list.items():
            final_text += f"`{key}.` {display_text}\n"
        return final_text.strip('\n')
    def get_style_list_text(self):
        return self.__get_list_text__(styles)
    def get_graph_list_text(self):
        return self.__get_list_text__(graphs)
        
        
    def getBotunlockedInStr(self):
        if self.get_table() is None or self.get_table().is_freed or self.get_table().get_races() is None or len(self.get_table().get_races()) < 12:
            return None
        
        time_passed_since_lounge_finish = datetime.now() - self.loungeFinishTime
        cooldown_time = time_passed_since_lounge_finish - common.lounge_inactivity_time_period
        return "Bot will become unlocked " + humanize.naturaltime(cooldown_time)

    def updateLoungeFinishTime(self):
        if self.loungeFinishTime is None and self.is_table_loaded() and len(self.get_table()) >= 12:
            self.loungeFinishTime = datetime.now()

    async def update_table(self) -> bool:
        if not self.is_table_loaded():
            return Table.ROOM_LOAD_STATUS_CODES.NO_ROOM_LOADED
        status = await self.get_table().update()
        if status in Table.ROOM_LOAD_STATUS_CODES.SUCCESS_CODES:
            await DataTracker.RoomTracker.add_data(self)
            self.get_table().apply_tabler_adjustments()
            self.updateLoungeFinishTime()
        return status

        
    async def verify_room(self, load_me):
        to_find = load_me[0]

        beautiful_soup_room_top = await WiimmfiSiteFunctions.get_front_race_smart(to_find)
        if beautiful_soup_room_top is None:
            del beautiful_soup_room_top
            return False, None, None, None
        
        
        temp_test_before = beautiful_soup_room_top.find_all('th')
        temp_test = temp_test_before[0]
        while len(temp_test_before) > 0:
            del temp_test_before[0]
        
        
        created_when = str(temp_test.contents[2].string).strip()
        rxx = str(temp_test.contents[1][common.HREF_HTML_NAME]).split("/")[4]
        created_when = created_when[:created_when.index("ago)")+len("ago)")].strip()
        room_str = "Room " + str(temp_test.contents[1].text) + ": " + created_when + " - "
        last_match = str(temp_test.contents[6].string).strip("\n\t ")
        
        if len(last_match) == 0:
            room_str += "Not started"
        else:
            room_str += last_match
            
        player_data = {}
        correctLevel = beautiful_soup_room_top.next_sibling
        while isinstance(correctLevel, NavigableString):
            correctLevel = correctLevel.next_sibling
        
        
        
        if correctLevel is None:
            return False, None, None, None
        
        
        while True:
            correctLevel = correctLevel.next_sibling
            
            if correctLevel is None:
                break
            if isinstance(correctLevel, NavigableString):
                continue
            if 'id' in correctLevel.attrs:
                break
            player_items = correctLevel.find_all('td')
            
            player_items_iterable = iter(player_items)
            FC_data_str = str(next(player_items_iterable).contents[0].text).strip()
            
            
            place_in_room = next(player_items_iterable).contents[0]
            place_in_room_str = ""
            if isinstance(place_in_room, NavigableString):
                place_in_room_str = str(place_in_room.string)
            elif isinstance(place_in_room, Tag):
                place_in_room_str = str(place_in_room.text)
        
            place_in_room_str = place_in_room_str.lower().strip("\u2007. hostviewrgu\n\t")
            del place_in_room
            
            mii_classes = correctLevel.find_all(class_="mii-font")
            if len(place_in_room_str) == 0 or len(mii_classes) != 1 or not UtilityFunctions.is_fc(FC_data_str):
                player_data[FC_data_str] = ("bad data", "bad data")
                common.log_text(str(place_in_room_str), common.ERROR_LOGGING_TYPE)
                common.log_text(str(mii_classes), common.ERROR_LOGGING_TYPE)
                common.log_text(str(FC_data_str), common.ERROR_LOGGING_TYPE)
                
            else:
                if mii_classes[0] is None or len(mii_classes[0]) < 1:
                    player_data[FC_data_str] = ("bad data", "bad data")
                    common.log_text(str(mii_classes), common.ERROR_LOGGING_TYPE)
                    common.log_text(str(mii_classes[0]), common.ERROR_LOGGING_TYPE)
                else:
                    player_data[FC_data_str] = (place_in_room_str, str(mii_classes[0].contents[0]))
            
            while len(mii_classes) > 0:
                del mii_classes[0]
        return True, player_data, room_str, rxx
    
    
    async def load_room_smart(self, load_me, is_vr_command=False, message_id=None, setup_discord_id=0, setup_display_name=""):
        rxx, room_races = await WiimmfiSiteFunctions.get_races_smart(load_me)
        if rxx is None:
            return Table.ROOM_LOAD_STATUS_CODES.DOES_NOT_EXIST
        if len(room_races) == 0: # Couldn't find room or no races played (hasn't finished first race)
            return Table.ROOM_LOAD_STATUS_CODES.HAS_NO_RACES
        table = Table.Table(rxx, room_races, message_id, setup_discord_id, setup_display_name)
        self.set_table(table)
        #M ake call to database to add data
        if not is_vr_command:
            await DataTracker.RoomTracker.add_data(self)
        self.get_table().apply_tabler_adjustments()
        
        return Table.ROOM_LOAD_STATUS_CODES.SUCCESS
            
    
    def updatedLastUsed(self):
        self.last_used = datetime.now()
        self.updateLoungeFinishTime()
        
    def updateWPCoolDown(self):
        self.lastWPTime = datetime.now()
        
    def shouldSendNoticiation(self) -> bool:
        if self.get_war() is not None:
            return self.should_send_mii_notification
        return False
    
    def setShouldSendNotification(self, should_send_mii_notification):
        self.should_send_mii_notification = should_send_mii_notification

    def getWPCooldownSeconds(self) -> int:
        if self.should_send_mii_notification:
            self.should_send_mii_notification = False
        if common.in_testing_server:
            return -1
        if self.lastWPTime is None:
            return -1
        curTime = datetime.now()
        time_passed = curTime - self.lastWPTime
        return common.wp_cooldown_seconds - int(time_passed.total_seconds())
    
    
    def updateRLCoolDown(self):
        self.roomLoadTime = datetime.now()

    def getRLCooldownSeconds(self) -> int:
        if common.in_testing_server:
            return -1
        if self.roomLoadTime is None:
            return -1
        curTime = datetime.now()
        time_passed = curTime - self.roomLoadTime
        return common.mkwx_page_cooldown_seconds - int(time_passed.total_seconds())
        
        
    def isFinishedLounge(self) -> bool:
        if not self.is_table_loaded():
            return True
        
        if self.get_table().is_freed:
            return True
        
        if self.lastWPTime is not None:
            time_passed_since_last_wp = datetime.now() - self.lastWPTime
            if time_passed_since_last_wp > common.inactivity_unlock:
                return True
            
        time_passed_since_last_used = datetime.now() - self.last_used
        if time_passed_since_last_used > common.inactivity_unlock:
            return True

        
        if self.loungeFinishTime is None:
            return False
        
        time_passed_since_lounge_finish = datetime.now() - self.loungeFinishTime
        return time_passed_since_lounge_finish > common.lounge_inactivity_time_period
        
    def freeLock(self):
        if self.get_table() is not None:
            self.get_table().is_freed = True

    def isInactive(self):
        curTime = datetime.now()
        time_passed_since_last_used = curTime - self.last_used
        return time_passed_since_last_used > common.inactivity_time_period
    



    # ========================== Save state functionality ==============================
    def get_save_state(self, command="Unknown Command"):
        save_state = {}
        save_state["War"] = self.get_war().get_recoverable_save_state()
        save_state["Room"] = self.get_table().get_recoverable_save_state()
        save_state["graph"] = self.graph
        save_state["race_size"] = self.race_size
        save_state["style"] = self.style
        return (command, save_state)
    
    def add_save_state(self, command="Unknown Command", save_state=None):
        if save_state is None:
            command, save_state = self.get_save_state(command)
        
        self.save_states = self.save_states[:self.state_pointer+1] #clear all "redo" states
        self.save_states.append((command, save_state)) #append new state
        self.state_pointer += 1 #increment state pointer (state pointer always points to previous save state)

    #Function that removes the last save state - does not restore it
    def remove_last_save_state(self):
        if len(self.save_states) < 1 or self.state_pointer < 0:
            return False
        command, _ = self.save_states.pop(self.state_pointer)
        return command
    
    #removes last "redo"
    def remove_last_redo_state(self):
        if len(self.save_states) <1 or self.state_pointer+1 >= len(self.save_states):
            return False
        
        return self.save_states.pop(self.state_pointer+1)[0]
    
    def get_undo_list(self):
        ret = "Undoable commands:"
        undos = self.save_states[:self.state_pointer+1]
        if len(undos)==0:
            return "No commands to undo."
        
        for i, (command, _) in enumerate(undos[::-1]):
            ret+=f"\n   {i+1}. `{command}`"
        
        return ret
    
    def get_redo_list(self):
        ret = "Redoable commands:"
        redos = self.save_states[self.state_pointer+1:-1]
        if len(redos)==0:
            return "No commands to redo."

        for i, (command, _) in enumerate(redos):
            ret+=f"\n   {i+1}. `{command}`"
        
        return ret
        
    #restores previous state (?undo)
    def restore_last_save_state(self, do_all=False):
        if len(self.save_states) < 1 or self.state_pointer < 0:
            return False

        if self.state_pointer+1 == len(self.save_states):
            self.add_save_state(command=None) #save the current state before reverting to the previous state if it hasn't been saved yet
            self.state_pointer-=1
        
        if do_all:
            self.state_pointer = 0
        
        command, save_state = self.save_states[self.state_pointer]
        self.state_pointer-=1

        
        self.get_table().restore_save_state(save_state["Room"])
        self.get_war().restore_save_state(save_state["War"])
        self.graph = save_state["graph"]
        self.style = save_state["style"]
        self.race_size = save_state["race_size"]
        return command
    
    #restores to the following state (?redo)
    def restore_last_redo_state(self, do_all=False):
        if len(self.save_states) <1 or self.state_pointer+2 >= len(self.save_states):
            return False
            
        if do_all:
            self.state_pointer=len(self.save_states)-2
        else:
            if self.state_pointer+2 < len(self.save_states):
                self.state_pointer+=1

        command, save_state = self.save_states[self.state_pointer][0], self.save_states[self.state_pointer+1][1]
        
        self.get_table().restore_save_state(save_state["Room"])
        self.get_war().restore_save_state(save_state["War"])
        self.graph = save_state["graph"]
        self.style = save_state["style"]
        self.race_size = save_state["race_size"]
        return command

    def unload_table(self):
        if self.get_table() is not None:
            self.get_table().destroy()
        self.set_table(None)
    

    # ======================== Reset / cleaning up / "Deconstruction" ================
    def reset(self, server_id):
        self.unload_table()
        self.set_war(None)
        self.prev_command_sw = False
        self.manualWarSetUp = False
        self.last_used = datetime.now()
        self.loungeFinishTime = None
        # Don't reset these, these are needed to prevent abuse to Wiimmfi and Lorenzi's site
        # self.lastWPTime = None
        # self.roomLoadTime = None
        self.save_states = []
        self.state_pointer = -1
        self.should_send_mii_notification = True
        self.set_style_and_graph(server_id)
        self.race_size = 4
        

        
