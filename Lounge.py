'''
Created on Jun 29, 2021

@author: willg
'''
import dill as pkl
import os
from datetime import datetime, timedelta
from common import lounge_channel_mappings, LoungeUpdateChannels





DEFAULT_UPDATE_COOLDOWN_TIME = timedelta(seconds=20)
class Lounge:
    def __init__(self, id_counter_file, table_reports_file, server_id, update_cooldown_time=DEFAULT_UPDATE_COOLDOWN_TIME):
        self.table_reports = {}
        self.table_id_counter = 25 #set at a slightly higher number so the first few submissions aren't confusing for people
        
        self.id_counter_file = id_counter_file
        self.table_reports_file = table_reports_file
        self.load_pkl()
        
        self.server_id = server_id
        
        if self.server_id not in lounge_channel_mappings:
            raise Exception("Created a Lounge abomination")
        
        self.channels_mapping:LoungeUpdateChannels = lounge_channel_mappings[self.server_id]
        
        
        
        self.update_cooldowns = {}
        self.update_cooldown_time = update_cooldown_time
        
    
    def get_user_update_submit_cooldown(self, author_id):
        if author_id not in self.update_cooldowns:
            return -1
    
        curTime = datetime.now()
        time_passed = curTime - self.update_cooldowns[author_id]
        return int(self.update_cooldown_time.total_seconds()) - int(time_passed.total_seconds())
    
    def add_counter(self):
        self.table_id_counter += 1
    def get_counter(self):
        return self.table_id_counter
    
    def add_report(self, report_id, sent_message, summary_channel_id):
        self.table_reports[report_id] = [sent_message.id, sent_message.channel.id, summary_channel_id, "PENDING"]
    
    def clear_user_cooldown(self, author):
        self.update_cooldowns.pop(author.id, None)
        
    def update_user_cooldown(self, author):
        self.update_cooldowns[author.id] = datetime.now()
    
    def get_primary_information(self):
        return (self.channels_mapping.updater_channel_id_primary,
                self.channels_mapping.updater_link_primary,
                self.channels_mapping.preview_link_primary,
                self.channels_mapping.type_text_primary)
    
    def get_secondary_information(self):
        return (self.channels_mapping.updater_channel_id_secondary,
                self.channels_mapping.updater_link_secondary,
                self.channels_mapping.preview_link_secondary,
                self.channels_mapping.type_text_secondary)
    
    def get_information(self, is_primary=True):
        return self.get_primary_information() if is_primary else self.get_secondary_information()
    

    def __load__(self, table_reports, table_id_counter):
        self.table_reports = table_reports
        self.table_id_counter = table_id_counter
        
    
    def load_pkl(self):
        if len(self.table_reports) == 0:
            if os.path.exists(self.id_counter_file):
                with open(self.id_counter_file, "rb") as pickle_in:
                    try:
                        self.table_id_counter = pkl.load(pickle_in)
                    except:
                        print("Could not read in the pickle for lounge update table counter.")
                        
            
            if os.path.exists(self.table_reports_file):
                with open(self.table_reports_file, "rb") as pickle_in:
                    try:
                        self.table_reports = pkl.load(pickle_in)
                    except:
                        print("Could not read in the pickle for lounge update tables.")


    def dump_pkl(self):
        if len(self.table_reports) > 0:
            with open(self.id_counter_file, "wb") as pickle_out:
                try:
                    pkl.dump(self.table_id_counter, pickle_out)
                except:
                    print("Could not dump pickle for counter ID. Current counter", self.table_id_counter)
                    
            with open(self.table_reports_file, "wb") as pickle_out:
                try:
                    pkl.dump(self.table_reports, pickle_out)
                except:
                    print("Could not dump counter dictionary. Current dict:", self.table_reports)
                    