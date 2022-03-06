"""
Created on Jun 29, 2021

@author: willg
"""
import dill as pkl
import os
from datetime import datetime, timedelta
from typing import Set
import common
from collections import namedtuple

MKW_LOUNGE_RT_UPDATE_PREVIEW_LINK = "https://www.mkwlounge.gg/ladder/tabler.php?ladder_type=rt&event_data="
MKW_LOUNGE_CT_UPDATE_PREVIEW_LINK = "https://www.mkwlounge.gg/ladder/tabler.php?ladder_type=ct&event_data="
MKW_LOUNGE_RT_UPDATER_LINK = MKW_LOUNGE_RT_UPDATE_PREVIEW_LINK
MKW_LOUNGE_CT_UPDATER_LINK = MKW_LOUNGE_CT_UPDATE_PREVIEW_LINK
MKW_LOUNGE_RT_UPDATER_CHANNEL = 758161201682841610
MKW_LOUNGE_CT_UPDATER_CHANNEL = 758161224202059847

UpdateChannels = namedtuple(
    "UpdateChannels",
    [
        "updater_channel_id_primary",
        "updater_link_primary",
        "preview_link_primary",
        "type_text_primary",
        "updater_channel_id_secondary",
        "updater_link_secondary",
        "preview_link_secondary",
        "type_text_secondary",
    ],
)

lounge_channel_mappings = {
    common.MKW_LOUNGE_SERVER_ID: UpdateChannels(
        updater_channel_id_primary=MKW_LOUNGE_RT_UPDATER_CHANNEL,
        updater_link_primary=MKW_LOUNGE_RT_UPDATER_LINK,
        preview_link_primary=MKW_LOUNGE_RT_UPDATE_PREVIEW_LINK,
        type_text_primary="RT",
        updater_channel_id_secondary=MKW_LOUNGE_CT_UPDATER_CHANNEL,
        updater_link_secondary=MKW_LOUNGE_CT_UPDATER_LINK,
        preview_link_secondary=MKW_LOUNGE_CT_UPDATE_PREVIEW_LINK,
        type_text_secondary="CT",
    ),
    common.TABLE_BOT_DISCORD_SERVER_ID: UpdateChannels(
        updater_channel_id_primary=common.TABLE_BOT_SERVER_BETA_TWO_CHANNEL_ID,
        updater_link_primary=MKW_LOUNGE_RT_UPDATER_LINK,
        preview_link_primary=MKW_LOUNGE_RT_UPDATE_PREVIEW_LINK,
        type_text_primary="RT",
        updater_channel_id_secondary=common.TABLE_BOT_SERVER_BETA_TWO_CHANNEL_ID,
        updater_link_secondary=MKW_LOUNGE_CT_UPDATER_LINK,
        preview_link_secondary=MKW_LOUNGE_CT_UPDATE_PREVIEW_LINK,
        type_text_secondary="CT",
    ),
}


DEFAULT_UPDATE_COOLDOWN_TIME = timedelta(seconds=20)


class Lounge:
    def __init__(
        self,
        id_counter_file,
        table_reports_file,
        server_id,
        report_authority_check,
        update_cooldown_time=DEFAULT_UPDATE_COOLDOWN_TIME,
    ):
        self.table_reports = {}
        self.table_id_counter = 1

        self.id_counter_file = id_counter_file
        self.table_reports_file = table_reports_file
        self.load_pkl()

        self.server_id = server_id

        self.report_table_authority_check = report_authority_check

        if self.server_id not in lounge_channel_mappings:
            raise Exception("Created a Lounge abomination")

        self.channels_mapping: UpdateChannels = lounge_channel_mappings[self.server_id]

        self.update_cooldowns = {}
        self.update_cooldown_time = update_cooldown_time

    def get_user_update_submit_cooldown(self, author_id):
        if author_id not in self.update_cooldowns:
            return -1

        curTime = datetime.now()
        time_passed = curTime - self.update_cooldowns[author_id]
        return int(self.update_cooldown_time.total_seconds()) - int(
            time_passed.total_seconds()
        )

    def add_counter(self):
        self.table_id_counter += 1

    def get_counter(self):
        return self.table_id_counter

    def add_report(self, report_id, sent_message, summary_channel_id, json_data=None):
        self.table_reports[report_id] = [
            sent_message.id,
            sent_message.channel.id,
            summary_channel_id,
            "PENDING",
            json_data,
        ]

    def clear_user_cooldown(self, author):
        self.update_cooldowns.pop(author.id, None)

    def update_user_cooldown(self, author):
        self.update_cooldowns[author.id] = datetime.now()

    def has_submission_id(self, submissionID):
        return submissionID in self.table_reports

    def get_submission_id(self, submissionID):
        if len(self.table_reports[submissionID]) == 4:  # To support legacy submissions
            return [*self.table_reports[submissionID], None]
        return self.table_reports[submissionID]

    def get_submission_id_json_data(self, submissionID):
        if len(self.table_reports[submissionID]) == 4:
            return None
        return self.table_reports[submissionID][4]

    def submission_id_of_last_matching_json(self, submissionID):
        json_data = self.get_submission_id_json_data(submissionID)
        if json_data is None:
            return None
        for sub_id in reversed(self.table_reports):
            if sub_id < submissionID and json_data == self.get_submission_id_json_data(
                sub_id
            ):
                return sub_id
        return None  # redundant, but putting this here for novice Python devs

    def remove_submission_id(self, submissionID):
        self.table_reports.pop(submissionID, None)

    def approve_submission_id(self, submissionID):
        self.table_reports[submissionID][3] = "APPROVED"

    def deny_submission_id(self, submissionID):
        self.table_reports[submissionID][3] = "DENIED"

    def submission_id_is_pending(self, submissionID):
        return (
            self.has_submission_id(submissionID)
            and self.table_reports[submissionID][3] == "PENDING"
        )

    def submission_id_is_denied(self, submissionID):
        return (
            self.has_submission_id(submissionID)
            and self.table_reports[submissionID][3] == "DENIED"
        )

    def submission_id_is_approved(self, submissionID):
        return (
            self.has_submission_id(submissionID)
            and self.table_reports[submissionID][3] == "APPROVED"
        )

    def get_updater_channel_ids(self) -> Set[int]:
        return {
            self.channels_mapping.updater_channel_id_primary,
            self.channels_mapping.updater_channel_id_secondary,
        }

    def get_primary_information(self):
        return (
            self.channels_mapping.updater_channel_id_primary,
            self.channels_mapping.updater_link_primary,
            self.channels_mapping.preview_link_primary,
            self.channels_mapping.type_text_primary,
        )

    def get_secondary_information(self):
        return (
            self.channels_mapping.updater_channel_id_secondary,
            self.channels_mapping.updater_link_secondary,
            self.channels_mapping.preview_link_secondary,
            self.channels_mapping.type_text_secondary,
        )

    def get_information(self, is_primary=True):
        return (
            self.get_primary_information()
            if is_primary
            else self.get_secondary_information()
        )

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
                        print(
                            "Could not read in the pickle for lounge update table counter."
                        )

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
                    print(
                        "Could not dump pickle for counter ID. Current counter",
                        self.table_id_counter,
                    )

            with open(self.table_reports_file, "wb") as pickle_out:
                try:
                    pkl.dump(self.table_reports, pickle_out)
                except:
                    print(
                        "Could not dump counter dictionary. Current dict:",
                        self.table_reports,
                    )
