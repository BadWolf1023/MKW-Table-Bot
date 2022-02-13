'''
Created on Jul 30, 2020

@author: willg
'''
from collections import defaultdict
import WiimmfiSiteFunctions
import SmartTypes
import Room
import War
from datetime import datetime
import humanize
import common
from typing import Dict, Tuple, Union, List
import ServerFunctions
import asyncio
from data_tracking import DataTracker
import TimerDebuggers


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
last_wp_message = {}
last_sug_view = {}
active_components = defaultdict(list)

class ChannelBot(object):
    '''
    classdocs
    '''
    def __init__(self, prev_command_sw=False, room=None, war=None, manualWarSetup=False, server_id=None, channel_id=None):
        self.room:Room.Room = room
        self.war:War.War = war
        self.prev_command_sw = prev_command_sw
        self.manualWarSetUp = manualWarSetup
        self.last_used = datetime.now()
        self.loungeFinishTime = None
        self.lastWPTime = None
        self.roomLoadTime = None
        self.save_states = []
        self.state_pointer = -1
        self.resolved_errors = set()
        
        self.should_send_mii_notification = True
        self.set_style_and_graph(server_id)
        self.set_dc_points(server_id)
        self.server_id = server_id
        self.channel_id = channel_id
        self.race_size = 4

    def is_table_loaded(self) -> bool:
        return self.room is not None and self.war is not None
        
    def get_race_size(self):
        return self.race_size
    def get_room(self):
        return self.room
    def get_war(self):
        return self.war
    def get_prev_command_sw(self):
        return self.prev_command_sw
    def get_manual_war_set_up(self):
        return self.manualWarSetUp
    def get_last_used(self):
        return self.last_used
    def get_lounge_finish_time(self):
        return self.loungeFinishTime
    def get_last_wptime(self):
        return self.lastWPTime
    def get_room_load_time(self):
        return self.roomLoadTime
    def get_save_states(self):
        return self.save_states
    def get_redo_states(self):
        return self.redo_save_states
    def get_should_send_mii_notification(self):
        return self.should_send_mii_notification
    def get_server_id(self):
        return self.server_id
    def get_channel_id(self):
        return self.channel_id
    def get_graph(self):
        return self.graph
    def get_style(self):
        return self.style
    def get_dc_points(self):
        return self.dc_points
    
    def get_resolved_errors(self):
        return self.resolved_errors
    
    def player_to_dc_num(self, race, player):
        GPs = self.getWar().getNumberOfGPS()
        dc_list = self.getRoom().get_dc_list_players(GPs)

        return dc_list.index((race, player))+1
    
    def player_to_num(self, player):
        players = self.getRoom().get_sorted_player_list()
        players = [player[0] for player in players]

        return players.index(player)+1

    def get_room_started_message(self):
        started_war_str = "FFA started" if self.getWar().isFFA() else "War started"
        if self.getWar().ignoreLargeTimes:
            started_war_str += " (ignoring errors for large finish times)"
        started_war_str += f". {self.getRoom().getRXXText()}"
        return started_war_str
        
    def set_race_size(self, new_race_size:int):
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
        if self.is_table_loaded() or self.room.is_freed or len(self.room.races) < 12:
            return None
        
        time_passed_since_lounge_finish = datetime.now() - self.loungeFinishTime
        cooldown_time = time_passed_since_lounge_finish - common.lounge_inactivity_time_period
        return "Bot will become unlocked " + humanize.naturaltime(cooldown_time)
            
    def updateLoungeFinishTime(self):
        if self.loungeFinishTime is None and self.is_table_loaded() and len(self.room.races) >= 12:
            self.loungeFinishTime = datetime.now()
    
    @TimerDebuggers.timer_coroutine
    async def update_table(self) -> WiimmfiSiteFunctions.RoomLoadStatus:
        if not self.is_table_loaded():
            return WiimmfiSiteFunctions.RoomLoadStatus(WiimmfiSiteFunctions.RoomLoadStatus.NO_ROOM_LOADED)
            
        status = await self.room.update()
        if status:
            await DataTracker.RoomTracker.add_data(self)  # Must come before adjustments are applied
            self.room.apply_tabler_adjustments()
            self.updateLoungeFinishTime()
            asyncio.create_task(self.room.populate_miis())  # Must come after adjustments are applied
        return status
        
    async def verify_room_smart(self, smart_type: SmartTypes.SmartLookupTypes) -> Tuple[WiimmfiSiteFunctions.RoomLoadStatus, Union[None, Room.Race.Race]]:
        status_code, front_race = await WiimmfiSiteFunctions.get_front_race_smart(smart_type, hit_lounge_api=True)
        return status_code, front_race
    
    @TimerDebuggers.timer_coroutine
    async def load_table_smart(self, smart_type: SmartTypes.SmartLookupTypes, war, message_id=None, setup_discord_id=0, setup_display_name="") -> WiimmfiSiteFunctions.RoomLoadStatus:
        status, rxx, room_races = await WiimmfiSiteFunctions.get_races_smart(smart_type, hit_lounge_api=True)
        if not status:
            return status
        self.reset()
        room = Room.Room(rxx, room_races, message_id, setup_discord_id, setup_display_name)
        self.setWar(war)
        self.setRoom(room)
        asyncio.create_task(self.room.populate_miis()) # We can create this task before adjustments are applied since calling this load_room_smart function loads a new room (with no real tabler adjustments)
        # Make call to database to add data
        await DataTracker.RoomTracker.add_data(self)
        if self.getWar() is None:  # The caller should have ensured that a war is set - dangerous game to play!
            return WiimmfiSiteFunctions.RoomLoadStatus(WiimmfiSiteFunctions.RoomLoadStatus.SUCCESS_BUT_NO_WAR)
        return WiimmfiSiteFunctions.RoomLoadStatus(WiimmfiSiteFunctions.RoomLoadStatus.SUCCESS)

    async def add_room_races(self, rxx, room_races):
        if not self.is_table_loaded():
            return WiimmfiSiteFunctions.RoomLoadStatus(WiimmfiSiteFunctions.RoomLoadStatus.NO_ROOM_LOADED)
        if rxx is None:
            return WiimmfiSiteFunctions.RoomLoadStatus(WiimmfiSiteFunctions.RoomLoadStatus.DOES_NOT_EXIST)
        if len(room_races) == 0: # Couldn't find room or no races played (hasn't finished first race)
            return WiimmfiSiteFunctions.RoomLoadStatus(WiimmfiSiteFunctions.RoomLoadStatus.HAS_NO_RACES)
        self.room.add_races(rxx, room_races)
        # Make call to database to add data
        await DataTracker.RoomTracker.add_data(self)
        self.room.apply_tabler_adjustments()
        asyncio.create_task(self.room.populate_miis()) # We must create this task after adjustments are applied since the adjustments applied to the new races may affect which miis we pull
        if self.getWar() is None:  # The caller should have ensured that a war is set - dangerous game to play!
            return WiimmfiSiteFunctions.RoomLoadStatus(WiimmfiSiteFunctions.RoomLoadStatus.SUCCESS_BUT_NO_WAR)
        return WiimmfiSiteFunctions.RoomLoadStatus(WiimmfiSiteFunctions.RoomLoadStatus.SUCCESS)
            
    
    def setRoom(self, room):
        self.room = room
        self.updateLoungeFinishTime()
        
    def getRoom(self) -> Room.Room:
        return self.room
    
    def setWar(self, war):
        self.war = war
    def getWar(self) -> War.War:
        return self.war
    
    # def add_pic_view(self, pic_view):
    #     view_ind = add_pic_view(pic_view)
    #     self.pic_views.append(view_ind)
    #     try:
    #         if len(self.pic_views)>1:
    #             to_delete = self.pic_views[:-1]

    #             delete_pic_views(to_delete)
    #             self.pic_views = self.pic_views[-1:]

    #     except IndexError:
    #         pass

    # def add_sug_view(self, sug_view):
    #     view_ind = add_sug_view(sug_view)
    #     self.sug_views.append(view_ind)
    #     try:
    #         if len(self.sug_views)>1:
    #             to_delete = self.sug_views[:-1]
    #             delete_sug_views(to_delete)
    #             self.sug_views = self.sug_views[-1:]

    #     except IndexError:
    #         pass
    
    def updatedLastUsed(self):
        self.last_used = datetime.now()
        self.updateLoungeFinishTime()
        
    def updateWPCoolDown(self):
        self.lastWPTime = datetime.now()
        
    def shouldSendNoticiation(self) -> bool:
        if self.is_table_loaded():
            return self.should_send_mii_notification
        return False
    
    def setShouldSendNotification(self, should_send_mii_notification):
        self.should_send_mii_notification = should_send_mii_notification

    def getWPCooldownSeconds(self) -> int:
        if self.should_send_mii_notification:
            self.should_send_mii_notification = False
        # if common.in_testing_server:
        #     return -1
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
        if self.getRoom() is None or not self.getRoom().is_initialized():
            return True
        
        if self.room.is_freed:
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
        if self.is_table_loaded():
            self.room.is_freed = True
            #self.room.set_up_user = None
            #self.room.set_up_user_display_name = ""
            #self.loungeFinishTime = None

    def isInactive(self):
        curTime = datetime.now()
        time_passed_since_last_used = curTime - self.last_used
        return time_passed_since_last_used > common.inactivity_time_period
    
    def get_save_state(self, command="Unknown Command"):
        save_state = {}
        save_state["War"] = self.getWar().get_recoverable_save_state()
        save_state["Room"] = self.getRoom().get_recoverable_save_state()
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

        
        self.getRoom().restore_save_state(save_state["Room"])
        self.getWar().restore_save_state(save_state["War"])
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
        
        self.getRoom().restore_save_state(save_state["Room"])
        self.getWar().restore_save_state(save_state["War"])
        self.graph = save_state["graph"]
        self.style = save_state["style"]
        self.race_size = save_state["race_size"]
        return command

    async def clear_last_wp_button(self):
        try:
            await last_wp_message[self.channel_id].edit(view=None)
            last_wp_message.pop(self.channel_id, None)
        except:
            pass
    
    def add_sug_view(self, view):
        # self.clear_last_sug_view()
        last_sug_view[self.channel_id] = view

    def clear_last_sug_view(self):
        try:
            view = last_sug_view.pop(self.channel_id, None)
            if view: 
                asyncio.create_task(view.on_timeout())
        except Exception:
            pass
    
    def add_component(self, component):
        active_components[self.channel_id].append(component)
    
    def clear_all_components(self):
        components = active_components.pop(self.channel_id, [])
        for c in components:
            try:
                asyncio.create_task(c.on_timeout())
            except Exception:
                pass

    def unload_table(self):
        if self.is_table_loaded():
            self.room.destroy()
        self.setRoom(None)
        self.setWar(None)
    
    def destroy(self):
        asyncio.create_task(self.clear_last_wp_button())
        self.clear_last_sug_view()
        self.clear_all_components()
        self.unload_table()

    def reset(self):
        self.destroy()
        self.room = None
        self.war = None
        self.prev_command_sw = False
        self.manualWarSetUp = False
        self.last_used = datetime.now()
        self.loungeFinishTime = None
        #Don't reset these, these are needed to prevent abuse to Wiimmfi and Lorenzi's site
        #self.lastWPTime = None
        #self.roomLoadTime = None
        self.save_states = []
        self.state_pointer = -1
        self.resolved_errors = set()
        self.should_send_mii_notification = True
        self.set_style_and_graph(self.server_id)
        self.race_size = 4

        
        
