# -*- coding: utf-8 -*-

"""
.. note::
"""

import os
import logging
import traceback

import sqlite3


def get_kwh_tbl_item_list():

    """
    # KWH_DATALOG table 設定
    """

    return [

        ( 'ID', 'INTEGER PRIMARY KEY AUTOINCREMENT' ), # auto

        ( 'TIME', 'INTEGER DEFAULT -1' ),
        ( 'MODE', 'INTEGER DEFAULT 0' ), # 0=dayly 1=hourly

        ( 'KWH', 'DOUBLE DEFAULT 0.0' ),

    ] # 既存の table に後から column を追加する場合は最後に追加


def get_jma_tbl_item_list():

    """
    # JMA_DATALOG table 設定
    """

    return [

        ( 'ID', 'INTEGER PRIMARY KEY AUTOINCREMENT' ), # auto

        ( 'TIME', 'INTEGER DEFAULT -1' ),
        ( 'MODE', 'INTEGER DEFAULT 0' ), # 0=dayly 1=hourly

        ( 'TEMP', 'DOUBLE DEFAULT 0.0' ),
        ( 'TEMPMIN', 'DOUBLE DEFAULT 0.0' ),
        ( 'TEMPMAX', 'DOUBLE DEFAULT 0.0' ),

        ( 'RAIN', 'DOUBLE DEFAULT 0.0' ),
        ( 'SUN', 'DOUBLE DEFAULT 0.0' ),

    ] # 既存の table に後から column を追加する場合は最後に追加


def db_connect_db(
    sqlite_file_path
):
    """
    # sqlite_file_path の connect を返します
    s@sqlite_file_path : .sqlite
    """

    sql_connect = None

    try:
        sql_connect = sqlite3.connect( sqlite_file_path )

    except:
        logging.error( traceback.format_exc() )

    return sql_connect


def db_execute_sql_cmd_args(
    sqlite_file_path,
    sql_cmd_args,
    text_factory=sqlite3.OptimizedUnicode
):
    """
    # sqlite_file_path の connect を返します
    s@sqlite_file_path : .sqlite
    s[]@sql_cmd_args :
    """

    sql_connect = db_connect_db( sqlite_file_path )
    sql_connect.text_factory = text_factory

    result = 0

    try:
        sql_connect.execute( *sql_cmd_args )
        sql_connect.commit()
        result = 1

    except sqlite3.OperationalError:
        logging.warning( traceback.format_exc() )
        logging.warning( sql_cmd_args )

    except:
        logging.error( traceback.format_exc() )

    finally:
        if sql_connect != None:
            sql_connect.close()

    return result


def db_create_table(
    sqlite_file_path,
    tbl_name,
    sqlite_tbl_name_item_list,
    exist_table_list=[],
):
    """
    # .sqlite の初期設定
    s@sqlite_file_path : .sqlite
    s@tbl_name :
    s[]@exist_table_list :  登録済みの table 名 list
    """

    if sqlite_file_path != None:

        sqlite_dir_path = os.path.dirname( sqlite_file_path )

        if not os.path.isdir( sqlite_dir_path ):
            os.makedirs( sqlite_dir_path )

        sql_cmd_line_list = []
        for tbl_name_item in sqlite_tbl_name_item_list:
            sql_cmd_line_list.append( ' '.join( tbl_name_item ) )

        # create table
        if not tbl_name in exist_table_list:
            sql_cmd = '''\
    CREATE TABLE IF NOT EXISTS {0} (
    {1}
    );
    '''
            sql_cmd = sql_cmd.format( tbl_name, ',\n'.join( sql_cmd_line_list ) )

            db_execute_sql_cmd_args( sqlite_file_path, [ sql_cmd ] )

        # add table items
        fetchall = db_fetchall(
            sqlite_file_path,
            'pragma table_info({0});'.format( tbl_name )
        )

        cur_table_item_name_list = []

        for item in fetchall:
            cur_table_item_name_list.append( item[1] )

        for tbl_name_item in sqlite_tbl_name_item_list:

            if not tbl_name_item[0] in cur_table_item_name_list:

                sql_cmd = 'ALTER TABLE {0} ADD {1};'.format( tbl_name, ' '.join( tbl_name_item ) )
                logging.info( 'ALTER TABLE : {0}'.format( sql_cmd ) )

                db_execute_sql_cmd_args( sqlite_file_path, [ sql_cmd ] )

    return 1


def db_insert_data(
    sqlite_file_path,
    tbl_name,
    tbl_data_list
):
    """
    # tbl_data_list を tbl_name に INSERT
    s@sqlite_file_path : .sqlite
    s@tbl_name :
    s[]@tbl_data_list : [ [ data_name, value ], ... ]
    """

    if sqlite_file_path == None:

        return 0

    col_list = [ data[0] for data in tbl_data_list ]
    col_str = ', '.join( col_list )

    val_tmp_list = [ '?' for data in tbl_data_list ]
    val_tmp_str = ', '.join( val_tmp_list )

    sql_cmd_tmp = 'INSERT INTO {0} ( {1} ) VALUES ( {2} );'.format( tbl_name, col_str, val_tmp_str )

    return db_execute_sql_cmd_args( sqlite_file_path, [ sql_cmd_tmp, [ data[1] for data in tbl_data_list ] ] )


def db_fetchall(
    sqlite_file_path,
    cmd
):
    """
    # cmd を実行して fetchall 結果を返す
    s@sqlite_file_path : .sqlite
    s@cmd :sql cmd
    """

    sql_connect = db_connect_db( sqlite_file_path )
    sql_cursor = sql_connect.cursor()

    sql_cursor.execute( cmd )

    return sql_cursor.fetchall()
