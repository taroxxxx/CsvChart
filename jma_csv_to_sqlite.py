# -*- coding: utf-8 -*-
"""
https://www.data.jma.go.jp/gmd/risk/obsdl/index.php

dayly: 日別値:
地点= 練馬
項目= 日平均気温,日最高気温,日最低気温,降水量の日合計,日照時間

hourly: 時別値:
地点= 練馬
項目= 気温,降水量,日照時間
"""
import io
import os
import re
import csv
import sys
import sqlite3
import datetime
import traceback

import _lib
import _sqlite


if __name__ == '__main__':

    try:

        def check_has_tgt_time_mode( db_file_path, tbl_name, tgt_time, mode ):

            """
            # 指定した TIME&MODE があれば 1 を返す
            s@db_file_path:
            s@tbl_name
            i@tgt_time:
            i@mode
            """

            sql_connect = sqlite3.connect( db_file_path )
            sql_cursor = sql_connect.cursor()

            sql_cursor.execute(
                'SELECT ID,TIME,MODE FROM {0} WHERE TIME={1} AND MODE={2};'.format( tbl_name, tgt_time, mode )
            )

            fetchone = sql_cursor.fetchone()
            sql_connect.close()

            return 0 if ( fetchone==None ) else 1


        def ___sqlite___():
            pass

        # CREATE TABLE IF NOT EXISTS, item が無い場合に ALTER TABLE ADD
        db_file_path = os.path.abspath( r'datalog.sqlite' )
        tbl_name = 'JMA_DATALOG'

        for item in [
            [ tbl_name, _sqlite.get_jma_tbl_item_list() ],
        ]:
            _sqlite.db_create_table( db_file_path, item[0], item[1] )


        def ___csv___():
            pass

        """
        dayly: 2019/11 ~ 2020/8
        hourly: 2020/7 ~ 2020/8
        """

        csv_file_path = os.path.abspath( r'nerima_hourly_20200701_20200831.csv' )
        mode = 1
        #mode = 1 if ( day != None ) else 0 # 0=dayly 1=hourly

        with open( csv_file_path ) as f:

            lines = csv.reader( f )

            for id, line in enumerate( lines ):

                if id < 6:
                    continue # columun 列 除外

                date_strs = line[0].split() # ####/##/##

                ymd = date_strs[0].split( '/' )  # ####/##/##
                cur_year = int( ymd[0] )
                cur_month = int( ymd[1] )
                cur_day = int( ymd[2] )

                cur_hour = 0
                cur_min = 0

                if mode: # 1=hourly
                    hm = date_strs[1].split( ':' ) # 00:00
                    cur_hour = int( hm[0] )
                    cur_min = int( hm[1] )

                temp = float( line[1] )

                temp_max = 0.0
                temp_min = 0.0
                if not mode: # 0=dayly
                    temp_max = float( line[4] )
                    temp_min = float( line[7] )

                rain = float( line[ 4 if mode else 10 ] )
                sun_str = line[ 7 if mode else 13 ]
                sun = float( sun_str ) if len( sun_str ) else 0.0

                tmp_hour = cur_hour
                if cur_hour == 24:
                    tmp_hour = 23 # hout = 0-23

                cur_d = datetime.datetime(
                    cur_year, cur_month, cur_day,
                    tmp_hour, cur_min, 0
                )

                if cur_hour == 24:
                    cur_d += datetime.timedelta( minutes=60 )

                tgt_time = int( _lib.datetime_to_time( cur_d ) )

                #print cur_d,temp,rain,sun
                #continue

                # 同じ 日付&mode のデータがあったらスルー
                if check_has_tgt_time_mode( db_file_path, tbl_name, tgt_time, mode ):
                    continue

                tbl_data_list = [

                    ( 'TIME', tgt_time ),
                    ( 'MODE', mode ),

                    ( 'TEMP', temp ),
                    ( 'TEMPMIN', temp_max ),
                    ( 'TEMPMAX', temp_min ),

                    ( 'RAIN', rain ),
                    ( 'SUN', sun ),

                ]

                _sqlite.db_insert_data( db_file_path, tbl_name, tbl_data_list )

    except:
        print traceback.format_exc()
    raw_input( '--- end ---' )
