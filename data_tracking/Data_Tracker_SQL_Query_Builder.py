'''
Created on Oct 29, 2021

@author: willg
'''


def get_fcs_in_Player_table(fcs):
    return f"""SELECT fc
FROM Player
WHERE fc in ({', '.join('?'*len(fcs))});"""




#print(get_fcs_not_in_Player_table([1, 2, 3]))