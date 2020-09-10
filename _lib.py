# -*- coding: utf-8 -*-

"""
.. note::
"""

import os
import re
import csv
import json
import time
import logging
import datetime
import subprocess


"""
https://docs.python.org/ja/2.7/library/csv.html#examples
"""

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')


def src_str_to_utf( src_str, on_err_result ):

    conv_utf = u''

    try:
        conv_utf = u'{0}'.format( src_str.decode( 'utf_8', 'ignore' ) )
    except:
        conv_utf = u'{0}'.format( on_err_result )

    return conv_utf


def date_str_to_datetime( date_str ):

    date_str_fmt = re.compile( r'(?P<y>[\d]+)-(?P<m>[\d]+)-(?P<d>[\d]+)' )
    date_str_search = date_str_fmt.search( date_str )

    if date_str_search != None:

        y = int( date_str_search.group( 'y' ) )
        m = int( date_str_search.group( 'm' ) )
        d = int( date_str_search.group( 'd' ) )

        return datetime.datetime( y,m,d )

    return None


def time_to_datetime( src_time ):

    """
    time@src_time
    """
    return datetime.datetime.fromtimestamp( src_time )


def datetime_to_time( src_d ):

    """
    datetime@src_d
    """
    return time.mktime( src_d.timetuple() )


def datetime_to_week_start_end_datatime( d ):

    """
    # d が含まれる週の 開始(月曜日),終了(金曜日) の datetime を返す

    @d : datetime
    """
    week_start_d = d + datetime.timedelta( days=range(0,-7,-1)[ d.weekday() ] ) # to mon
    week_end_d = d + datetime.timedelta( days=range(4,-3,-1)[ d.weekday() ] ) # to fri

    return week_start_d, week_end_d


def time_range_to_elapsed_str( start_time_sec, end_time_sec=None, day_disp=1, tmp='{hour:02d}:{min:02d}' ):

    """
    # 開始>終了 までの時間をテキストで返す

    i@start_time_sec : 開始 time
    i@end_time_sec : 終了 time
    i@day_disp : 0 では 経過時間、1 では　経過日数+時間 を表示
    s@tmp : テキストテンプレート
    """

    if end_time_sec == None:
        end_time_sec = time.time()

    elapsed_sec = ( end_time_sec - start_time_sec )
    elapsed_sec = 0.0 if elapsed_sec < 0.0 else elapsed_sec

    d = datetime.timedelta( seconds=elapsed_sec )

    min = d.seconds / ( 60 )

    days_str = '{0}days&'.format( d.days ) if day_disp and elapsed_sec > 60 * 60 * 24 * 1 else '' # over 1 days

    fmt_dict = {
        'hour' :( min / 60 ) if day_disp else 24 * d.days + ( min / 60 ),
        'min' : min % ( 60 ),
        'sec' : d.seconds % ( 60 ),
    }

    return '{0}{1}'.format( days_str, tmp.format( **fmt_dict ) )


def src_time_to_str( src_time, tmp=u'{month}/{day}({weekday_utf})' ):

    """
    # 入力時間をテキストで返す

    i@src_time : time
    s@tmp : テキストテンプレート
    """

    d = datetime.datetime.fromtimestamp( src_time )

    fmt_dict = {

        'year' : d.year,
        'y' : str( d.year )[2:],
        'month' : d.month,
        'day' : d.day,
        'weekday' : ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d.weekday()],
        'weekday_utf' : [u'月',u'火',u'水',u'木',u'金',u'土',u'日'][d.weekday()],
        'hour' : d.hour,
        'min' : d.minute,
        'sec' : d.second,
        'microsec' : d.microsecond,

    }

    return tmp.format( **fmt_dict ) if src_time else '-'*5


def get_round_time( interval_min=10 ):

    """
    # 指定分以下を切り捨てた time を返す

    i@interval_min : time
    """

    d = datetime.datetime.fromtimestamp( time.time() )

    return time.mktime(
        datetime.datetime(
            d.year, d.month, d.day, d.hour,
            d.minute - d.minute%interval_min,
        ).timetuple()
    )


def get_timeline_row(
    rowlabel,
    name,
    tooltip,
    time_start,
    time_end,
):

    """
    # timeline row を返します

    s@rowlabel : timeline でのラベル
    s@name : timeline でのデータ名
    i@time_start : timeline での開始日時
    i@time_end : timeline での終了日時
    """

    start_d = time_to_datetime( time_start )
    end_d = time_to_datetime( time_end )

    fmt_dict = {
        'label' : rowlabel,
        'name' : name,

        'tooltip' : tooltip,

        'sy' : start_d.year, 'smo' : start_d.month-1, 'sd' : start_d.day,
        'sh' : start_d.hour, 'sm' : start_d.minute,

        'ey' : end_d.year, 'emo' : end_d.month-1, 'ed' : end_d.day,
        'eh' : end_d.hour, 'em' : end_d.minute,
    }

    line_tmp = u"""        ['{label}','{name}','{tooltip}',new Date({sy},{smo},{sd},{sh},{sm}),"""
    line_tmp += u"""new Date({ey},{emo},{ed},{eh},{em})]"""

    return line_tmp.format( **fmt_dict )


def get_calendar_row_list(
    pre_weeks=1,
    post_weeks=4,
    calendar_row_label='calendar',
):

    """
    # calendar_row_list を返します

    s@rowlabel : timeline でのラベル
    s@name : timeline でのデータ名
    i@time_start : timeline での開始日時
    i@time_end : timeline での終了日時
    """

    calendar_row_list = []

    d = time_to_datetime( time.time() )

    week_start_d, week_end_d = datetime_to_week_start_end_datatime( d )
    week_start_d = datetime.datetime( week_start_d.year,week_start_d.month,week_start_d.day,0,0,0 )
    week_end_d = datetime.datetime( week_end_d.year,week_end_d.month,week_end_d.day,23,59,59 )

    # datetime だと 月の日にち範囲を超えるとエラーになるので time で
    timeline_start_datetime = time_to_datetime( datetime_to_time( week_start_d ) - 60*60*24*7*pre_weeks )
    timeline_end_datetime = time_to_datetime( datetime_to_time( week_end_d ) + 60*60*24*7*post_weeks )

    timeline_end_time = datetime_to_time( timeline_end_datetime )


    def ___month___():
        pass

    cur_month_start_d = timeline_start_datetime

    while 1:

        # 月末を取得
        tmp_m = cur_month_start_d.month + 1 # 翌月
        tmp_y = cur_month_start_d.year + ( 1 if 12<tmp_m else 0 ) # < 12月なら翌年に
        tmp_m %= 12
        tmp_m = 12 if tmp_m==0 else tmp_m # 0 の時は 12 に

        next_month_start_d = datetime.datetime( tmp_y,tmp_m,1,0,0,0 ) # 翌月 1日
        cur_month_end_d = next_month_start_d - datetime.timedelta( minutes=1 ) # 月末 の 23:59:59

        cur_month_start_time = datetime_to_time( cur_month_start_d )
        cur_month_end_time = datetime_to_time( cur_month_end_d )

        if timeline_end_time < cur_month_end_time: # timeline 範囲内に
            cur_month_end_time = timeline_end_time

        calendar_row_list.append(
            get_timeline_row(
                calendar_row_label,
                u'{0}月'.format( cur_month_start_d.month ),
                u'{0}～{1}'.format(
                    u'{0}'.format( src_time_to_str( cur_month_start_time ) ),
                    u'{0}'.format( src_time_to_str( cur_month_end_time ) ),
                ),
                cur_month_start_time,
                cur_month_end_time
            )
        )

        if cur_month_end_time == timeline_end_time: # timeline 範囲いっぱい
            break

        cur_month_start_d = next_month_start_d


    def ___sat_sun___():
        pass

    sat_start_d = timeline_start_datetime + datetime.timedelta(
        days=[5,4,3,2,1,0,6][ timeline_start_datetime.weekday() ] # 翌土曜日に
    )
    sat_start_d = datetime.datetime( sat_start_d.year,sat_start_d.month,sat_start_d.day,0,0,0 )

    sun_end_d = sat_start_d + datetime.timedelta( days=1 ) # >日曜日
    sun_end_d = datetime.datetime( sun_end_d.year,sun_end_d.month,sun_end_d.day,23,59,59 )

    sat_start_t = datetime_to_time( sat_start_d )
    sun_end_t = datetime_to_time( sun_end_d )

    while 1:

        sat_start_d = time_to_datetime( sat_start_t )
        sun_end_d = time_to_datetime( sun_end_t )

        tooltip = u'{0}{1}{0}'.format(
            r'&nbsp;',
            u'{0}～{1}'.format(
                u'{0}'.format( src_time_to_str( datetime_to_time( sat_start_d ) ) ),
                u'{0}'.format( src_time_to_str( datetime_to_time( sun_end_d ) ) ),
            )
        )

        calendar_row_list.append(
            get_timeline_row(
                calendar_row_label,
                u'',
                tooltip,
                sat_start_t,
                sun_end_t
            )
        )

        # datetime だと 月の日にち範囲を超えるとエラーになるので time で
        sat_start_t += 60*60*24*7 # add1week
        sun_end_t += 60*60*24*7 # add1week

        if timeline_end_time < sat_start_t: # 土曜日が範囲外
            break

        if timeline_end_time < sun_end_t: # 日曜日が範囲外 = 期間内に修正
            sun_end_t = timeline_end_time


    def ___holidays___():
        pass

    json_file_path = os.path.join( os.path.abspath( r'C:\Users\taro\workData\Development\holidays.json' ) )

    preset_dict = {}
    with open( json_file_path, 'r' ) as f:
        preset_dict = json.load( f )

    for data_str_key in preset_dict.keys():

        d = date_str_to_datetime( data_str_key )

        # 範囲外
        if d<timeline_start_datetime or timeline_end_datetime<d:
            continue

        calendar_row_list.append(
            get_timeline_row(
                calendar_row_label,
                u'{0}'.format( preset_dict[ data_str_key ] ),
                u'{0}: {1}'.format( preset_dict[ data_str_key ], src_time_to_str( datetime_to_time( d ) ) ),
                datetime_to_time( datetime.datetime( d.year,d.month,d.day,0,0,0 ) ),
                datetime_to_time( datetime.datetime( d.year,d.month,d.day,23,59,59 ) )
            )
        )

    # This Week
    calendar_row_list.append(
        get_timeline_row(
            calendar_row_label,
            u'今週: {0}/{1}～{2}/{3}'.format(
                week_start_d.month, week_start_d.day, week_end_d.month, week_end_d.day
            ),
            u'{0}～{1}'.format(
                src_time_to_str( datetime_to_time( week_start_d ) ),
                src_time_to_str( datetime_to_time( week_end_d ) )
            ),
            datetime_to_time( week_start_d ),
            datetime_to_time( week_end_d )
        )
    )

    # Today
    d = time_to_datetime( time.time() )
    calendar_row_list.append(
        get_timeline_row(
            calendar_row_label,
            u'今日',
            u'{0}'.format( src_time_to_str( time.time() ) ),
            datetime_to_time( datetime.datetime( d.year,d.month,d.day,0,0,0 ) ),
            datetime_to_time( datetime.datetime( d.year,d.month,d.day,23,59,59 ) )
        )
    )

    return timeline_start_datetime, timeline_end_datetime, calendar_row_list


def get_html_line_tmp():

    html_line_tmp = u'''\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>{title}</title>
<head>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">google.charts.load("current", {{packages:["timeline", "corechart"]}});</script>
{timeline_line}
</head>
<body>
    <right><font Size="1">updated: {updated}</font></right><br>
{timeline_body_line}
</body>
</html>
'''

    return html_line_tmp


def get_html_timeline_data_line_tmp():

    timeline_data_line_tmp = u'''\
<script type="text/javascript">
google.charts.setOnLoadCallback(drawChart);
function drawChart() {{
    var dataTable = new google.visualization.DataTable();
    dataTable.addColumn({{ type: 'string', id: 'RowLabel' }});
    dataTable.addColumn({{ type: 'string', id: 'Name' }});
    dataTable.addColumn({{ type: 'string', role: 'tooltip' }});
    dataTable.addColumn({{ type: 'date', id: 'Start' }});
    dataTable.addColumn({{ type: 'date', id: 'End' }});

    dataTable.addRows([
{data_line}
    ]);
    var options = {{
        timeline: {{
            colorByRowLabel: false, showBarLabels: true, groupByRowLabel: true,
            showRowLabels: true, rowLabelStyle: {{fontSize: 11.0}},
            showBarLabels: true, barLabelStyle: {{fontSize: 11.0}},
        }},
        avoidOverlappingGridLines: false,
        tooltip: {{isHtml: true}}{colors}
    }};
    var chart = new google.visualization.Timeline(document.getElementById('{chart_name}'));
    chart.draw(dataTable, options);
    }}
</script>
'''

    return timeline_data_line_tmp


def get_html_chart_body_line_tmp():

    chart_body_line_tmp = u'''    <div id="{chart_name}" style="height: {height}px;"></div>'''

    """
    dataTable.addColumn({{ type: 'string', role: 'tooltip' }});
    """

    return chart_body_line_tmp
