# -*- coding: utf-8 -*-
"""
refer: http://s-kawakami.hatenablog.jp/entry/2017/05/21/032253

user.json
{
  "username": "username",
  "password": "pass",
  "requestspath": "/requests-2.7.0"
}

"""
import io
import os
import re
import sys
import json
import sqlite3
import datetime
import traceback
#import csv
#import json
#import argparse
#from pprint import pprint
#from urllib.parse import quote

tmp_dict = {}
with open( os.path.abspath( 'user.json' ) ) as f:
    tmp_dict = json.load( f )

USERNAME = tmp_dict[ 'username' ]
PASSWORD = tmp_dict[ 'password' ]

"""
https://pypi.org/project/requests/2.7.0/
sys.path[0:0] = [ r'C:\Users\taro\workData\GitHub\requests' ]
"""
sys.path[0:0] = [ tmp_dict[ 'requestspath' ] ]
import requests


import _lib
import _sqlite


if __name__ == '__main__':

    try:

        def update_tgt_time_kwh( db_file_path, tbl_name, tgt_time, kwh, mode ):

            """
            # 指定した TIME があれば KWH を更新
            s@db_file_path:
            s@tbl_name
            i@tgt_time:
            f@kwh
            i@mode
            """

            # update last data's DATA
            sql_connect = sqlite3.connect( db_file_path )
            sql_cursor = sql_connect.cursor()

            sql_cursor.execute(
                'SELECT ID,TIME,MODE FROM {0} WHERE TIME={1} AND MODE={2};'.format( tbl_name, tgt_time, mode )
            )
            fetchone = sql_cursor.fetchone()

            if fetchone == None: # No Data
                sql_connect.close()
                return 0

            tgt_id = fetchone[0] # [ ID,TIME,MODE ]

            cmd ='UPDATE {0} SET KWH={1} WHERE ID={2};'.format( tbl_name, kwh, tgt_id )
            sql_cursor.execute( cmd )
            #print cmd

            sql_connect.commit()
            sql_connect.close()

            return 1


        def ___sqlite___():
            pass

        # CREATE TABLE IF NOT EXISTS, item が無い場合に ALTER TABLE ADD
        db_file_path = os.path.abspath( r'datalog.sqlite' )
        kwh_tbl_name = 'KWH_DATALOG'

        for item in [
            [ kwh_tbl_name, _sqlite.get_kwh_tbl_item_list() ],
        ]:
            _sqlite.db_create_table( db_file_path, item[0], item[1] )


        def ___requests___():
            pass

        # ログイン情報設定


        session = requests.Session()

        url = 'https://www.kurashi.tepco.co.jp/kpf-login'

        # ログイン 念のため一度トップページへアクセスして cookie を食べる
        loginparam = {
            'ACCOUNTUID': USERNAME,
            'PASSWORD': PASSWORD,
            'HIDEURL': '/pf/ja/pc/mypage/home/index.page?',
            'LOGIN': 'EUAS_LOGIN',
        }

        loginheader = {
            'Referer': url,
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        session.get( url )
        login = session.post( url, data=loginparam, headers=loginheader )

        # CSV 取得前に使用量ページの cookie を食べておく必要があるようなのでリクエストを投げる
        session.get( 'https://www.kurashi.tepco.co.jp/pf/ja/pc/mypage/learn/comparison.page' )

        def ___range___():
            pass
        """
        dayly: 2019/11 ~ 2020/8
        hourly: 2020/7 ~ 2020/8
        """
        year = 2020
        month_list = [ 7 ] #range( 1, 8+1, 1 )
        day_list = [ None ] #range( 1,31+1,1) #

        # URL を組み立てて CSV データを取ってくる
        csv_url_head = 'https://www.kurashi.tepco.co.jp/pf/ja/pc/mypage/learn/comparison.page?ReqID=CsvDL&year={0}'
        csv_url_head = csv_url_head.format( year )

        for month in month_list:

            for day in day_list:

                mode = 1 if ( day != None ) else 0 # 0=dayly 1=hourly

                if mode:
                    csv_url = '{0}&month={1:02d}&day={2:02d}'.format( csv_url_head, month, day )
                else:
                    csv_url = '{0}&month={1:02d}'.format( csv_url_head, month )

                print csv_url

                csvgetheader = {
                    'Referer': 'https://www.kurashi.tepco.co.jp/pf/ja/pc/mypage/learn/comparison.page',
                }
                csvdata = session.get( csv_url, headers=csvgetheader )
                lines = _lib.unicode_csv_reader( io.StringIO( initial_value=csvdata.text ) )

                for id, line in enumerate( lines ):

                    if id == 0:
                        continue # columun 列 除外

                    date_strs = line[4].split() # ####/##/## 00:00

                    ymd = date_strs[0].split( '/' )  # ####/##/##
                    cur_year = int( ymd[0] )
                    cur_month = int( ymd[1] )
                    cur_day = int( ymd[2] )

                    cur_hour = 0
                    cur_min = 0

                    if mode:

                        hm = date_strs[1].split( ':' ) # 00:00
                        cur_hour = int( hm[0] )
                        cur_min = int( hm[1] )

                    if line[8] == '---': # NoData
                        continue

                    kwh = float( line[8] )

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

                    # 同じ日付のデータがあったら更新
                    update_tgt_time_kwh( db_file_path, kwh_tbl_name, tgt_time, kwh, mode )

                    tbl_data_list = [
                        ( 'TIME', tgt_time ),
                        ( 'MODE', mode ),
                        ( 'KWH', kwh ),
                    ]

                    _sqlite.db_insert_data( db_file_path, kwh_tbl_name, tbl_data_list )

    except:
        print traceback.format_exc()
    raw_input( '--- end ---' )
