'''
Created on Apr 3, 2021

@author: willg
'''
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from discord import Embed, File
import UtilityFunctions
import os as operatingsystem
import cv2
import UserDataProcessing
import numpy as np
import common


class Mii(KaitaiStruct):

    mii_color_dict = {0:16458773, #dark red
                  1:16741914, #orange
                  2:16771361, #yellow
                  3:10153261, #light green
                  4:33073, #Dark green
                  5:741043, #dark blue
                  6:4831457, #light blue
                  7:16736895, #pink
                  8:8858539, #dark purple
                  9:5717272, #Brown
                  10:16777214, #White
                  11:0 #Black
                  }


    def __init__(self, _io, mii_data_hex_str, folder_path, file_name, FC, _parent=None, _root=None):
        self.mii_data_hex_str = mii_data_hex_str
        self.file_name = file_name 
        self.folder_path = folder_path
        self.FC = FC
        self.lounge_name = UserDataProcessing.lounge_get(self.FC)
        self.cropped = False
        self._io = KaitaiStream(BytesIO(_io))
        self._parent = _parent
        self._root = _root if _root else self
        self._read()
    
    def update_lounge_name(self):
        self.lounge_name = UserDataProcessing.lounge_get(self.FC)

    def _read(self):
        self.invalid = self._io.read_bits_int_be(1) != 0
        self.gender = self._io.read_bits_int_be(1) != 0
        self.birth_month = self._io.read_bits_int_be(4)
        self.birth_day = self._io.read_bits_int_be(5)
        self.favorite_color = self._io.read_bits_int_be(4)
        self.favorite = self._io.read_bits_int_be(1) != 0
        self._io.align_to_byte()
        self.mii_name = self._io.read_bytes(20).decode(u"utf-16be")
        self.mii_name, _, _ = self.mii_name.partition('\x00')
        self.mii_name = self.mii_name.strip()
        self.body_height = self._io.read_u1()
        self.body_weight = self._io.read_u1()
        self.avatar_id = [None] * (4)
        for i in range(4):
            self.avatar_id[i] = self._io.read_u1()

        self.client_id = [None] * (4)
        for i in range(4):
            self.client_id[i] = self._io.read_u1()

        self.face_type = self._io.read_bits_int_be(3)
        self.face_color = self._io.read_bits_int_be(3)
        self.facial_feature = self._io.read_bits_int_be(4)
        self.unknown = self._io.read_bits_int_be(3)
        self.mingle = self._io.read_bits_int_be(1) != 0
        self.unknown_2 = self._io.read_bits_int_be(1) != 0
        self.downloaded = self._io.read_bits_int_be(1) != 0
        self.hair_type = self._io.read_bits_int_be(7)
        self.hair_color = self._io.read_bits_int_be(3)
        self.hair_flip = self._io.read_bits_int_be(1) != 0
        self.unknown_3 = self._io.read_bits_int_be(5)
        self.eyebrow_type = self._io.read_bits_int_be(5)
        self.unknown_4 = self._io.read_bits_int_be(1) != 0
        self.eyebrow_rotation = self._io.read_bits_int_be(4)
        self.unknown_5 = self._io.read_bits_int_be(6)
        self.eyebrow_color = self._io.read_bits_int_be(3)
        self.eyebrow_size = self._io.read_bits_int_be(4)
        self.eyebrow_vertical = self._io.read_bits_int_be(5)
        self.eyebrow_horizontal = self._io.read_bits_int_be(4)
        self.eye_type = self._io.read_bits_int_be(6)
        self.unknown_6 = self._io.read_bits_int_be(2)
        self.eye_rotation = self._io.read_bits_int_be(3)
        self.eye_vertical = self._io.read_bits_int_be(5)
        self.eye_color = self._io.read_bits_int_be(3)
        self.unknown_7 = self._io.read_bits_int_be(1) != 0
        self.eye_size = self._io.read_bits_int_be(3)
        self.eye_horizontal = self._io.read_bits_int_be(4)
        self.unknown_8 = self._io.read_bits_int_be(5)
        self.nose_type = self._io.read_bits_int_be(4)
        self.nose_size = self._io.read_bits_int_be(4)
        self.nose_vertical = self._io.read_bits_int_be(5)
        self.unknown_9 = self._io.read_bits_int_be(3)
        self.mouth_type = self._io.read_bits_int_be(5)
        self.mouth_color = self._io.read_bits_int_be(2)
        self.mouth_size = self._io.read_bits_int_be(4)
        self.mouth_vertical = self._io.read_bits_int_be(5)
        self.glasses_type = self._io.read_bits_int_be(4)
        self.glasses_color = self._io.read_bits_int_be(3)
        self.unknown_10 = self._io.read_bits_int_be(1) != 0
        self.glasses_size = self._io.read_bits_int_be(3)
        self.glasses_vertical = self._io.read_bits_int_be(5)
        self.facial_hair_mustache = self._io.read_bits_int_be(2)
        self.facial_hair_beard = self._io.read_bits_int_be(2)
        self.facial_hair_color = self._io.read_bits_int_be(3)
        self.facial_hair_size = self._io.read_bits_int_be(4)
        self.facial_hair_vertical = self._io.read_bits_int_be(5)
        self.mole_enable = self._io.read_bits_int_be(1) != 0
        self.mole_size = self._io.read_bits_int_be(4)
        self.mole_vertical = self._io.read_bits_int_be(5)
        self.mole_horizontal = self._io.read_bits_int_be(5)
        self.unknown_11 = self._io.read_bits_int_be(1) != 0
        self._io.align_to_byte()
        self.creator_name = (self._io.read_bytes(20)).decode(u"utf-16be").replace("\x00","")
        self.creator_name, _, _ = self.creator_name.partition('\x00')
        self._io.read_bytes(14)
        self.country_id = self._io.read_u1()
        self.country_code = COUNTRY_CODES[self.country_id]
        
    def get_mii_embed(self):
        embed = Embed(
                    title = f"",
                    description="",
                    colour = Mii.mii_color_dict[self.favorite_color]
                )
        
        mii_name = UtilityFunctions.clean_for_output(self.mii_name)
        mii_name = mii_name if len(mii_name) > 0 else '\u200b'
        fc = self.FC if len(self.FC) > 0 else '\u200b'
        #print(f"Mii name: '{mii_name}'\nLen: {len(mii_name)}")
        #print(ord(mii_name))
        embed.add_field(name="**Mii Name**",value=mii_name)
        embed.add_field(name="**Gender**",value=f"{'Female' if self.gender else 'Male'}")
        
        embed.add_field(name="**FC**",value=fc)
        #file_name_id
        file = File(self.get_mii_picture_link())
        embed.set_image(url="attachment://" + self.file_name)
        return file, embed
    
    def get_mii_picture_link(self):
        return self.folder_path + self.file_name
    def get_mii_picture_path_for_table(self):
        return self.folder_path + common.MII_TABLE_PICTURE_PREFIX + self.file_name
    
    def main_mii_picture_exists(self):
        return operatingsystem.path.exists(self.get_mii_picture_link())
    def table_mii_picture_exists(self):
        return operatingsystem.path.exists(self.get_mii_picture_path_for_table())  
    
    def __remove_main_mii_picture__(self):
        if self.main_mii_picture_exists():
            operatingsystem.remove(self.get_mii_picture_link())
    def __remove_table_mii_picture__(self):
        if self.table_mii_picture_exists():
            operatingsystem.remove(self.get_mii_picture_path_for_table())
    def has_table_picture_file(self):
        return self.table_mii_picture_exists()
    
    def clean_up(self):
        """Removes the files it has a record of"""
        self.__remove_main_mii_picture__()
        self.__remove_table_mii_picture__()
        
    def output_table_mii_to_disc(self):
        if not self.main_mii_picture_exists():
            return False
        try:
            filled_mii_image = self.__fill_transparent_background_with_color__(background_color=common.DEFAULT_FOOTER_COLOR)
            resized_mii_image = self.__resize_mii_image__(mii_image=filled_mii_image, width=common.MII_SIZE_FOR_TABLE, height=common.MII_SIZE_FOR_TABLE)
            cv2.imwrite(self.get_mii_picture_path_for_table(), resized_mii_image)
            return True
        except:
            return False
    
    def get_table_mii_picture_cv2(self):
        if self.table_mii_picture_exists():
            try: #Race condition possible that the file no longer exists
                return self.__get_table_cv2_mii_image__()
            except:
                pass #We pass so we can try to output the main image to table image
            
        output_successful = self.output_table_mii_to_disc()
        if not output_successful:
            return None
        try: #Avoid race condition that the file no longer exists
            return self.__get_table_cv2_mii_image__()
        except:
            return None
    
    def __get_cv2_mii_image__(self):
        return cv2.imread(self.get_mii_picture_link(), cv2.IMREAD_UNCHANGED)
    
    def __get_table_cv2_mii_image__(self):
        return cv2.imread(self.get_mii_picture_path_for_table(), cv2.IMREAD_UNCHANGED)
    
    
    #Mutates given numpy array image with all transparency replaced with given background color
    #If no image is given, tries to open the main mii image and returns that as a numpy array with all transparent color replaced with the given background color
    def __fill_transparent_background_with_color__(self, mii_image=None, background_color=common.DEFAULT_FOOTER_COLOR):
        if mii_image is None:
            mii_image = self.__get_cv2_mii_image__()
            
        alpha_channel = mii_image[:,:,3]
        where_alpha_channel_transparent = np.where(alpha_channel<255, True, False)
        if len(background_color) == 3: #Missing alpha channel
            background_color = (*background_color, 255)
        mii_image[where_alpha_channel_transparent] = background_color
        
        return mii_image
    
    def __resize_mii_image__(self, mii_image=None, width=common.MII_SIZE_FOR_TABLE, height=common.MII_SIZE_FOR_TABLE):
        if mii_image is None:
            mii_image = self.__get_cv2_mii_image__()
        return cv2.resize(mii_image, dsize=(width, height), interpolation=cv2.INTER_AREA)
    
    """
    def get_cropped_image_for_table(self, mii_image=None, left_crop=LEFT_MII_CROP_AMOUNT, right_crop=RIGHT_MII_CROP_AMOUNT, top_crop=TOP_MII_CROP_AMOUNT, bottom_crop=BOTTOM_MII_CROP_AMOUNT):
        failure_result = False, None
        if mii_image is None:
            mii_image = self.get_cv2_mii_image()
        if len(mii_image) != Mii.MII_IMAGE_HEIGHT:
            return failure_result
        if len(mii_image[0]) != Mii.MII_IMAGE_WIDTH:
            return failure_result
        
        if len(mii_image) - top_crop - bottom_crop < 1: #The crop amount would result in a 0 or negative height picture
            return failure_result
        if len(mii_image[0]) - left_crop - right_crop < 1: #The crop amount would result in a 0 or negative width picture
            return failure_result
        
        cropped_mii_image = mii_image[top_crop:len(mii_image)-bottom_crop, left_crop:len(mii_image[0])-right_crop]
        return True, cropped_mii_image

    def remove_noise(self, mii_image=None, background_color=DEFAULT_BACKGROUND_COLOR):
        if mii_image is None:
            mii_image = self.mii_image
        
        mii_image = np.copy(mii_image)
            
        where_white_pixels = np.any(mii_image == [255, 255, 255, 1], axis=-1)
        mii_image[where_white_pixels] = background_color
        return True, mii_image
    """

COUNTRY_CODES = {
    0: None,
    1:'JP',
    2:'AQ',
    3:'NL',
    4:'FK',
    5:'GB',
    6:'GB',
    7:'SX',
    8:'AI',
    9:'AG',
    10:'AR',
    11:'AW',
    12:'BS',
    13:'BB',
    14:'BZ',
    15:'BO',
    16:'BR',
    17:'VG',
    18:'CA',
    19:'KY',
    20:'CL',
    21:'CO',
    22:'CR',
    23:'DM',
    24:'DO',
    25:'EC',
    26:'SV',
    27:'GF',
    28:'GD',
    29:'GP',
    30:'GT',
    31:'GY',
    32:'HT',
    33:'HN',
    34:'JM',
    35:'MQ',
    36:'MX',
    37:'MS',
    38:'AN',
    39:'NI',
    40:'PA',
    41:'PY',
    42:'PE',
    43:'KN',
    44:'LC',
    45:'VC',
    46:'SR',
    47:'TT',
    48:'TC',
    49:'US',
    50:'UY',
    51:'VI',
    52:'VE',
    53:'AM',
    54:'BY',
    55:'GE',
    56:'XK',
    57:'AK',
    58:'AH',
    59:'NY',
    62:'AX',
    63:'FO',
    64:'AL',
    65:'AU',
    66:'AT',
    67:'BE',
    68:'BA',
    69:'BW',
    70:'BG',
    71:'HR',
    72:'CY',
    73:'CZ',
    74:'DK',
    75:'EE',
    76:'FI',
    77:'FR',
    78:'DE',
    79:'GR',
    80:'HU',
    81:'IS',
    82:'IE',
    83:'IT',
    84:'LV',
    85:'LS',
    86:'LI',
    87:'LT',
    88:'LU',
    89:'MK',
    90:'MT',
    91:'ME',
    92:'MZ',
    93:'NA',
    94:'NL',
    95:'NZ',
    96:'NO',
    97:'PL',
    98:'PT',
    99:'RO',
    100:'RU',
    101:'RS',
    102:'SK',
    103:'SI',
    104:'ZA',
    105:'ES',
    106:'SZ',
    107:'SE',
    108:'CH',
    109:'TR',
    110:'GB',
    111:'ZM',
    112:'ZW',
    113:'AZ',
    114:'MR',
    115:'ML',
    116:'NE',
    117:'TD',
    118:'SD',
    119:'ER',
    120:'DJ',
    121:'SO',
    122:'AD',
    123:'GI',
    124:'GG',
    125:'IM',
    126:'JE',
    127:'MC',
    128:'TW',
    129:'KH',
    130:'LA',
    131:'MN',
    132:'MM',
    133:'NP',
    134:'VN',
    135:'KP',
    136:'KR',
    137:'BD',
    138:'BT',
    139:'BN',
    140:'MV',
    141:'LK',
    142:'TL',
    143:'IO',
    144:'HK',
    145:'MO',
    146:'CK',
    147:'NU',
    148:'NF',
    149:'MP',
    150:'AS',
    151:'GU',
    152:'ID',
    153:'SG',
    154:'TH',
    155:'PH',
    156:'MY',
    157:'BL',
    158:'MF',
    159:'PM',
    160:'CN',
    161:'AF',
    162:'KZ',
    163:'KG',
    164:'PK',
    165:'TJ',
    166:'TM',
    167:'UZ',
    168:'AE',
    169:'IN',
    170:'EG',
    171:'OM',
    172:'QA',
    173:'KW',
    174:'SA',
    175:'SY',
    176:'BH',
    177:'JO',
    178:'IR',
    179:'IQ',
    180:'IL',
    181:'LB',
    182:'PS',
    183:'YE',
    184:'SM',
    185:'VS',
    186:'BM',
    187:'PF',
    188:'RE',
    189:'YT',
    190:'NC',
    191:'WF',
    192:'NG',
    193:'AO',
    194:'GH',
    195:'TG',
    196:'BJ',
    197:'BF',
    198:'CI',
    199:'LR',
    200:'SL',
    201:'GN',
    202:'GW',
    203:'SN',
    204:'GM',
    205:'CV',
    206:'SH',
    207:'MD',
    208:'UA',
    209:'CM',
    211:'CD',
    212:'CG',
    213:'GQ',
    214:'GA',
    215:'ST',
    216:'DZ',
    217:'ET',
    218:'LY',
    219:'MA',
    220:'SS',
    221:'TN',
    222:'EH',
    223:'CU',
    224:'BI',
    225:'KM',
    226:'KE',
    227:'MG',
    228:'MW',
    229:'MU',
    230:'RW',
    231:'SC',
    232:'TZ',
    233:'UG',
    234:'FR',
    235:'PN',
    236:'GB',
    237:'GS',
    238:'FM',
    239:'FJ',
    240:'KI',
    241:'MH',
    242:'NR',
    243:'PW',
    244:'PG',
    245:'WS',
    246:'SB',
    247:'TK',
    248:'TO',
    249:'TV',
    250:'VU',
    251:'CX',
    252:'CC',
    253:'PR',
    254:'GL'
}     