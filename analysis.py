# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
datalog.sqlite からチャートを作成

datetime 指定が必要
"""

import os
import re
import sys
import copy
import time
import json
import codecs
#import psutil
import logging
import datetime
import traceback
import xmlrpclib


import sqlite3

from threading import Thread
from operator import itemgetter

import _lib
import _sqlite

class Analysis( object ):

    def __init__( self, db_file_path, main_logger=None ):



        self.chart_start_time = int( _lib.datetime_to_time( datetime.datetime( 2019,11,1 ) ) )
        self.chart_end_time = int( _lib.datetime_to_time( datetime.datetime( 2021,1,7 ) ) )
        self.interval_min = int( 60*24 ) # 1day



        self.db_file_path = db_file_path
        self.main_logger = logging if main_logger==None else main_logger # MonitorMain .main_logger

        self.avg_count = 10

        def ___html___():
            pass

        self.html_line_tmp = u'''\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>{title}</title>
<head>
<script type="text/javascript" src="https://www.google.com/jsapi"></script>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">google.charts.load("current", {{packages:["timeline", "corechart"]}});</script>
{script_lines}
</head>
<body>
    <right><font Size="1">updated: {updated}</font></right><br>
    <hr width="100%" size="0">
{div_lines}
</body>
</html>
'''

        self.drawchart_line_tmp = u'''\
<script type="text/javascript">
google.load("visualization", "1", {{packages:["corechart"]}});
google.setOnLoadCallback(drawChart);
function drawChart() {{
    var data = google.visualization.arrayToDataTable([
{columns}
{datarows}
    ]);
    var options = {{
        title: '{chartname}',
        areaOpacity: 0.0,
        series: {{{seriesOptions}}},
        vAxes: {{{vAxesOptions}}},
        chartArea:{{left:60,top:50,width:'90.0%',height:'80.0%'}},{colors}
    }};
    var chart = new google.visualization.{chart}(document.getElementById('{chartelmidid}'));
    chart.draw(data, options);
}}
</script>'''

        self.tr_line_tmp = u'''\
        <div id="{chartname_a}" style="width: 1800px; height: {height}px;"></div>
        '''


    def append_up_to_count( self, src_list, value, count ):

        tmp_list = copy.copy( src_list )

        if count < len( tmp_list ):
            tmp_list = tmp_list[1:] # 最初のを削除
        tmp_list.append( value ) # 追加
        tmp_list = tmp_list[-count:] # 移動平均数にまるめる

        return tmp_list


    def time_to_newdate( self, src_time ):

        """
        # 入力 src_time を google.charts の date で返す
        i@src_time : time
        """

        # datetime
        d = datetime.datetime.fromtimestamp( src_time )
        newdate_tmp = 'new Date({year:04d},{month},{day},{hour},{min})'

        fmt_dict = {
            'year' : d.year,
            'month' : d.month-1, # Google TimeLine の月は 0 start
            'day' : d.day,
            'hour' : d.hour,
            'min' : d.minute,
        }

        newdate = newdate_tmp.format( **fmt_dict )

        return newdate


    def get_column_labels( self, column_label_list ):

        """
        # data row の column label を返します
        s[]@column_label_list : labels
        """

        column_label_list = [ u"'{0}'".format( item ) for item in column_label_list ]
        column_labels = u'        [{0}],'.format( u', '.join( column_label_list ) )

        return column_labels


    def get_date_chart_row(
        self,
        newdate,
        val_list
    ):

        """
        # H軸 date の chart row を返します

        s@newdate: google.charts の date
        f[]@val_list : 値
        """

        val_str_list = [ '{0}'.format( val ) for val in val_list ]
        datarow = ', '.join( [ newdate ] + val_str_list)
        datarow = '        [{0}]'.format( datarow )

        return datarow


    def get_kwh_datalog_datas( self ):

        """
        kwh_mode_str_list:
        [ '', '', ... ]

        time_key_to_kwh_datas_dict:
        dict[ time_key ][ kwh_mode_str_list.index( drive_strs ) ] = {}
        """

        def ___variable___():
            pass

        kwh_tbl_name = 'KWH_DATALOG'


        def ___sqlite___():
            pass

        # get table data
        sqlite_data_list = _sqlite.db_fetchall(
            self.db_file_path,
            'SELECT * FROM {0};'.format( kwh_tbl_name )
        )

        sqlite_tbl_name_index_list = [ item[0] for item in _sqlite.get_kwh_tbl_item_list() ]

        time_key_to_kwh_datas_dict = {}

        for sqlite_data in sqlite_data_list:

            cur_time = sqlite_data[ sqlite_tbl_name_index_list.index( 'TIME' ) ]
            # print _lib.src_time_to_str( cur_time )
            time_key = '{0}'.format( cur_time )

            if not time_key_to_kwh_datas_dict.has_key( time_key ):
                time_key_to_kwh_datas_dict[ time_key ] = [ {}, {} ] # 0=dayly 1=hourly

            mode = sqlite_data[ sqlite_tbl_name_index_list.index( 'MODE' ) ] # 0=dayly 1=hourly
            kwh = sqlite_data[ sqlite_tbl_name_index_list.index( 'KWH' ) ]

            time_key_to_kwh_datas_dict[ time_key ][ mode ] = {

                'kwh': kwh,

            }

        return [ 'dayly', 'hourly' ], time_key_to_kwh_datas_dict


    def get_jma_datalog_datas( self ):

        """
        jma_mode_str_list:
        [ '', '', ... ]

        time_key_to_jma_datas_dict:
        dict[ time_key ][ kwh_mode_str_list.index( drive_strs ) ] = {}
        """

        def ___variable___():
            pass

        tbl_name = 'JMA_DATALOG'


        def ___sqlite___():
            pass

        # get table data
        sqlite_data_list = _sqlite.db_fetchall(
            self.db_file_path,
            'SELECT * FROM {0};'.format( tbl_name )
        )

        sqlite_tbl_name_index_list = [ item[0] for item in _sqlite.get_jma_tbl_item_list() ]

        time_key_to_jma_datas_dict = {}

        for sqlite_data in sqlite_data_list:

            #print sqlite_data

            date = sqlite_data[ sqlite_tbl_name_index_list.index( 'TIME' ) ]
            time_key = '{0}'.format( date )

            if not time_key_to_jma_datas_dict.has_key( time_key ):
                time_key_to_jma_datas_dict[ time_key ] = [ {}, {} ] # 0=dayly 1=hourly

            mode = sqlite_data[ sqlite_tbl_name_index_list.index( 'MODE' ) ] # 0=dayly 1=hourly

            temp = sqlite_data[ sqlite_tbl_name_index_list.index( 'TEMP' ) ]
            temp_min = sqlite_data[ sqlite_tbl_name_index_list.index( 'TEMPMIN' ) ]
            temp_max = sqlite_data[ sqlite_tbl_name_index_list.index( 'TEMPMAX' ) ]
            rain = sqlite_data[ sqlite_tbl_name_index_list.index( 'RAIN' ) ]
            sun = sqlite_data[ sqlite_tbl_name_index_list.index( 'SUN' ) ]
            #print temp

            time_key_to_jma_datas_dict[ time_key ][ mode ] = {

                'temp': temp,
                'temp_min': temp_min,
                'temp_max': temp_max,
                'rain': rain,
                'sun': sun,

            }

        return [ 'dayly', 'hourly' ], time_key_to_jma_datas_dict


    def create_chart(
        self,
        kwh_mode_str_list, time_key_to_kwh_datas_dict,
        jma_mode_str_list, time_key_to_jma_datas_dict,
    ):


        def get_datarow_list( chart_start_time, chart_end_time, interval_min, mode='kwh_temp' ):

            kwh_list = [ [],[] ] # 0=dayly 1=hourly
            temp_list = [ [],[] ] # 0=dayly 1=hourly
            temp_min_list = [ [],[] ] # 0=dayly 1=hourly
            temp_max_list = [ [],[] ] # 0=dayly 1=hourly

            kwh_temp_datarow_list = [ [],[] ] # 0=dayly 1=hourly

            for tgt_time in range( chart_start_time, chart_end_time+1, interval_min*60 ):

                tgt_time_key = '{0}'.format( tgt_time )
                newdate = self.time_to_newdate( tgt_time )

                if time_key_to_kwh_datas_dict.has_key( tgt_time_key ):

                    kwh_data_list = time_key_to_kwh_datas_dict[ tgt_time_key ]

                    jma_data_list = []

                    if time_key_to_jma_datas_dict.has_key( tgt_time_key ):
                        jma_data_list = time_key_to_jma_datas_dict[ tgt_time_key ]

                    for index, kwh_data_dict in enumerate( kwh_data_list ):

                        if len( kwh_data_dict.keys() ):

                            kwh = kwh_data_dict[ 'kwh' ]

                            kwh_list[ index ] = self.append_up_to_count( kwh_list[ index ], kwh, self.avg_count )

                            temp = 'null'
                            temp_min = 'null'
                            temp_max = 'null'
                            rain = 'null'
                            sun = 'null'

                            avg_temp = 'null'
                            avg_temp_min = 'null'
                            avg_temp_max = 'null'

                            if index < len( jma_data_list ):

                                jma_data_dict = jma_data_list[ index ]

                                if len( jma_data_dict.keys() ):

                                    temp = jma_data_dict[ 'temp' ]
                                    temp_min = jma_data_dict[ 'temp_min' ]
                                    temp_max = jma_data_dict[ 'temp_max' ]
                                    rain = jma_data_dict[ 'rain' ]
                                    sun = jma_data_dict[ 'sun' ]

                                    temp_list[ index ] = self.append_up_to_count(
                                        temp_list[ index ], temp, self.avg_count
                                    )
                                    temp_min_list[ index ] = self.append_up_to_count(
                                        temp_min_list[ index ], temp_min, self.avg_count
                                    )
                                    temp_max_list[ index ] = self.append_up_to_count(
                                        temp_max_list[ index ], temp_max, self.avg_count
                                    )

                                    avg_temp = (
                                        float( sum( temp_list[ index ] ) ) / float( len( temp_list[ index ] ) )
                                    )
                                    avg_temp_min = (
                                        float( sum( temp_min_list[ index ] ) ) / float( len( temp_min_list[ index ] ) )
                                    )
                                    avg_temp_max = (
                                        float( sum( temp_max_list[ index ] ) ) / float( len( temp_max_list[ index ] ) )
                                    )

                            val_list = []

                            if mode == 'kwh_temp':

                                val_list = [
                                    kwh,
                                    temp,
                                    temp_min,
                                    temp_max,
                                ]

                            elif mode == 'avg_kwh_temp':

                                val_list = [
                                    ( float( sum( kwh_list[ index ] ) ) / float( len( kwh_list[ index ] ) ) ),
                                    avg_temp,
                                    avg_temp_min,
                                    avg_temp_max,
                                ]

                            elif mode == 'rain_sun':

                                val_list = [
                                    rain,
                                    sun
                                ]

                            kwh_temp_datarow_list[ index ].append( self.get_date_chart_row(
                                newdate, val_list
                            ) )

            return kwh_temp_datarow_list


        drawchart_line_list = []
        div_line_list = []

        def ___dayly___():
            pass

        kwh_temp_datarow_list = get_datarow_list( self.chart_start_time, self.chart_end_time, self.interval_min, mode='kwh_temp' )
        rain_sun_datarow_list = get_datarow_list( self.chart_start_time, self.chart_end_time, self.interval_min, mode='rain_sun' )

        fmt_dict_tmp = {
            'chart': 'AreaChart',
            'vAxesOptions': '',
        }

        mode_str = 'dayly'

        fmt_dict_a = dict(fmt_dict_tmp, **{
            'columns': self.get_column_labels( [ 'datetiem', 'kwh', u'平均気温', u'最高気温', u'最低気温' ] ),
            'datarows': ',\n'.join( kwh_temp_datarow_list[0] ),
            'chartname': u'kwh/気温 ({0})'.format( mode_str ),
            'chartelmidid': 'kwh_temp_{0}'.format( mode_str ),
            'seriesOptions': '''
        0: {targetAxisIndex: 0, lineWidth: 2.0, pointSize: 3.0},
        1: {targetAxisIndex: 1, lineWidth: 1.0, pointSize: 0.0},
        2: {targetAxisIndex: 1, lineWidth: 1.0, pointSize: 0.0},
        3: {targetAxisIndex: 1, lineWidth: 1.0, pointSize: 0.0},
        ''',
            'vAxesOptions': '''
        0: {minValue: 0.0, maxValue: 20.0},
        1: {minValue: -10.0, maxValue: 40.0},
        2: {minValue: -10.0, maxValue: 40.0},
        3: {minValue: -10.0, maxValue: 40.0},
        ''',
            'colors' : "\n        colors: [ 'royalblue','darkgreen','tomato','skyblue' ]",
            'height' : 400,
        } )
        fmt_dict = dict(fmt_dict_a, **{
            'chartname_a': fmt_dict_a[ 'chartelmidid' ],
        } )
        drawchart_line_list.append( self.drawchart_line_tmp.format( **fmt_dict_a ) )
        div_line_list.append( self.tr_line_tmp.format( **fmt_dict ) )

        fmt_dict_a = dict(fmt_dict_tmp, **{
            'chart': 'SteppedAreaChart',
            'columns': self.get_column_labels( [ 'datetiem', u'降水量', u'日照時間' ] ),
            'datarows': ',\n'.join( rain_sun_datarow_list[0] ),
            'chartname': u'降水量/日照時間 ({0})'.format( mode_str ),
            'chartelmidid': 'rain_sun_{0}'.format( mode_str ),
            'seriesOptions': '''
        0: {targetAxisIndex: 0, lineWidth: 0.0, pointSize: 0.0, areaOpacity:0.75 },
        1: {targetAxisIndex: 1, lineWidth: 0.0, pointSize: 0.0, areaOpacity:0.25 },
        ''',
            'colors' : "\n        colors: [ 'blue', 'red' ]",
            'height' : 300,
        } )
        fmt_dict = dict(fmt_dict_a, **{
            'chartname_a': fmt_dict_a[ 'chartelmidid' ],
        } )
        rain_sun_drawchart_line = self.drawchart_line_tmp.format( **fmt_dict_a )
        rain_sun_div_line = self.tr_line_tmp.format( **fmt_dict )


        def ___avg_dayly___():
            pass

        kwh_temp_datarow_list = get_datarow_list(
            self.chart_start_time, self.chart_end_time, self.interval_min, mode='avg_kwh_temp'
        )
        """
        rain_sun_datarow_list = get_datarow_list(
            self.chart_start_time, self.chart_end_time, self.interval_min, mode='rain_sun'
        )
        """

        fmt_dict_tmp = {
            'chart': 'AreaChart',
            'vAxesOptions': '',
        }

        mode_str = 'dayly'

        fmt_dict_a = dict(fmt_dict_tmp, **{
            'columns': self.get_column_labels( [ 'datetiem', 'kwh', u'平均気温', u'最高気温', u'最低気温' ] ),
            'datarows': ',\n'.join( kwh_temp_datarow_list[0] ),
            'chartname': u'kwh/気温 ({0}) {1}日移動平均'.format( mode_str, self.avg_count ),
            'chartelmidid': 'avg_kwh_temp_{0}'.format( mode_str ),
            'seriesOptions': '''
        0: {targetAxisIndex: 0, lineWidth: 2.0, pointSize: 3.0},
        1: {targetAxisIndex: 1, lineWidth: 1.0, pointSize: 0.0},
        2: {targetAxisIndex: 1, lineWidth: 1.0, pointSize: 0.0},
        3: {targetAxisIndex: 1, lineWidth: 1.0, pointSize: 0.0},
        ''',
            'vAxesOptions': '''
        0: {minValue: 0.0, maxValue: 20.0},
        1: {minValue: -10.0, maxValue: 40.0},
        2: {minValue: -10.0, maxValue: 40.0},
        3: {minValue: -10.0, maxValue: 40.0},
        ''',
            'colors' : "\n        colors: [ 'royalblue','darkgreen','tomato','skyblue' ]",
            'height' : 400,
        } )
        fmt_dict = dict(fmt_dict_a, **{
            'chartname_a': fmt_dict_a[ 'chartelmidid' ],
        } )
        drawchart_line_list.append( self.drawchart_line_tmp.format( **fmt_dict_a ) )
        div_line_list.append( self.tr_line_tmp.format( **fmt_dict ) )
        """
        fmt_dict_a = dict(fmt_dict_tmp, **{
            'columns': self.get_column_labels( [ 'datetiem', u'降水量', u'日照時間' ] ),
            'datarows': ',\n'.join( rain_sun_datarow_list[0] ),
            'chartname': u'降水量/日照時間 ({0})'.format( mode_str ),
            'chartelmidid': 'rain_sun_{0}'.format( mode_str ),
            'seriesOptions': '''
        0: {targetAxisIndex: 0, lineWidth: 2.0, pointSize: 0.0},
        1: {targetAxisIndex: 1, lineWidth: 2.0, pointSize: 0.0},
        ''',
            'colors' : "\n        colors: [ 'skyblue', 'tomato' ]",
            'height' : 200,
        } )
        fmt_dict = dict(fmt_dict_a, **{
            'chartname_a': fmt_dict_a[ 'chartelmidid' ],
        } )
        drawchart_line_list.append( self.drawchart_line_tmp.format( **fmt_dict_a ) )
        div_line_list.append( self.tr_line_tmp.format( **fmt_dict ) )
        """


        def ___hourly___():
            pass
        """
        self.chart_start_time = int( _lib.datetime_to_time( datetime.datetime( 2020,7,1 ) ) )
        self.chart_end_time = int( _lib.datetime_to_time( datetime.datetime( 2020,8,31 ) ) )
        self.interval_min = int( 60 ) # 1hour

        kwh_temp_datarow_list = get_datarow_list( self.chart_start_time, self.chart_end_time, self.interval_min, mode='kwh_temp' )
        rain_sun_datarow_list = get_datarow_list( self.chart_start_time, self.chart_end_time, self.interval_min, mode='rain_sun' )

        fmt_dict_tmp = {
            'chart': 'AreaChart',
            'height' : 400,
        }

        mode_str = 'hourly'

        fmt_dict_a = dict(fmt_dict_tmp, **{
            'columns': self.get_column_labels( [ 'datetiem', 'kwh', u'平均気温', u'最高気温', u'最低気温' ] ),
            'datarows': ',\n'.join( kwh_temp_datarow_list[1] ),
            'chartname': u'kwh/気温 ({0})'.format( mode_str ),
            'chartelmidid': 'kwh_temp_{0}'.format( mode_str ),
            'seriesOptions': '''
        0: {targetAxisIndex: 0, lineWidth: 2.0, pointSize: 3.0, areaOpacity:0.0 },
        1: {targetAxisIndex: 1, lineWidth: 1.0, pointSize: 0.0, areaOpacity:0.0 },
        2: {targetAxisIndex: 1, lineWidth: 1.0, pointSize: 0.0, areaOpacity:0.0 },
        3: {targetAxisIndex: 1, lineWidth: 1.0, pointSize: 0.0, areaOpacity:0.0 },
        ''',
            'colors' : "\n        colors: [ 'royalblue','darkgreen','tomato','skyblue' ]",
        } )
        fmt_dict = dict(fmt_dict_a, **{
            'chartname_a': fmt_dict_a[ 'chartelmidid' ],
        } )
        drawchart_line_list.append( self.drawchart_line_tmp.format( **fmt_dict_a ) )
        div_line_list.append( self.tr_line_tmp.format( **fmt_dict ) )

        fmt_dict_a = dict(fmt_dict_tmp, **{
            'columns': self.get_column_labels( [ 'datetiem', u'降水量', u'日照時間' ] ),
            'datarows': ',\n'.join( rain_sun_datarow_list[1] ),
            'chartname': u'降水量/日照時間 ({0})'.format( mode_str ),
            'chartelmidid': 'rain_sun_{0}'.format( mode_str ),
            'seriesOptions': '''
        0: {targetAxisIndex: 0, lineWidth: 2.0, pointSize: 0.0},
        1: {targetAxisIndex: 1, lineWidth: 2.0, pointSize: 0.0},
        ''',
            'colors' : "\n        colors: [ 'skyblue', 'tomato' ]",
        } )
        fmt_dict = dict(fmt_dict_a, **{
            'chartname_a': fmt_dict_a[ 'chartelmidid' ],
        } )
        drawchart_line_list.append( self.drawchart_line_tmp.format( **fmt_dict_a ) )
        div_line_list.append( self.tr_line_tmp.format( **fmt_dict ) )
        """

        drawchart_line_list.append( rain_sun_drawchart_line )
        div_line_list.append( rain_sun_div_line )

        # html
        fmt_dict = {
            'title': 'Kwh State Chart',
            'script_lines' : '\n'.join( drawchart_line_list ),
            'div_lines' : '\n'.join( div_line_list ),
            'updated': _lib.src_time_to_str( time.time(), tmp=u'{month}/{day} {hour:02d}:{min:02d}'  ),
        }
        html_line = self.html_line_tmp.format( **fmt_dict )

        with codecs.open( os.path.abspath( r'tepco.html' ), 'w', 'utf-8' ) as f:
            f.write( html_line )

        return 1


def ___dev___():
    pass

if __name__ == '__main__':

    try:

        my_module = Analysis.__module__
        my_class = sys.modules[ my_module ].Analysis

        my_cls = my_class( os.path.abspath( r'datalog.sqlite' ) )

        kwh_mode_str_list, time_key_to_kwh_datas_dict = my_cls.get_kwh_datalog_datas()
        jma_mode_str_list, time_key_to_jma_datas_dict = my_cls.get_jma_datalog_datas()

        my_cls.create_chart(
            kwh_mode_str_list, time_key_to_kwh_datas_dict,
            jma_mode_str_list, time_key_to_jma_datas_dict,
        )

    except:

        logging.error( traceback.format_exc() )
    raw_input( '--- end ---' )
