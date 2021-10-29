'''
Created on Oct 29, 2021

@author: willg
'''


def get_fcs_in_Player_table(fcs):
    return f"""SELECT fc
FROM Player
WHERE fc in ({', '.join('?'*len(fcs))});"""

def get_insert_into_player_table_script():
    return """INSERT INTO Player (fc, pid, player_url)
VALUES(?, ?, ?);"""
    
def surround_script_begin_commit(script):
    return f"""BEGIN;
{script.rstrip(';')};
COMMIT;"""




#print(get_fcs_not_in_Player_table([1, 2, 3]))