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
        
    def get_mii_embed(self):
        embed = Embed(
                                            title = f"",
                                            description="",
                                            colour = Mii.mii_color_dict[self.favorite_color]
                                        )
        
        
        embed.add_field(name="**Mii Name**",value=f"{UtilityFunctions.filter_text(self.mii_name)}"+'\u200b')
        embed.add_field(name="**Gender**",value=f"{'Female' if self.gender else 'Male'}")
        embed.add_field(name="**FC**",value=self.FC+'\u200b')
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
        