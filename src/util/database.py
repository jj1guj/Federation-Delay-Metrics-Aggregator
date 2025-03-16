import logging
import os
import sqlite3
import sys
from logging import INFO, getLogger

logger = getLogger(__name__)
logger.setLevel(INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

dbname = './data/database.db'
conn = sqlite3.connect(dbname)
cur = conn.cursor()

# テーブルがなければ作成
cur.execute('''
CREATE TABLE IF NOT EXISTS summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id TEXT,
    note_created_at TEXT,
    note_received_at TEXT,
    diff INTEGER,
    instance_name TEXT,
    instance_host TEXT,
    instance_softwareName TEXT,
    instance_softwareVersion TEXT,
    created_at TEXT
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS error (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id TEXT,
    note_created_at TEXT,
    note_received_at TEXT,
    error TEXT,
    created_at TEXT
)
''')


def insert_summary(note_id, note_created_at, note_received_at, diff,
                   instance_name, instance_host, instance_softwareName,
                   instance_softwareVersion):
    try:
        logger.info(f"Inserting summary: {note_id}")
        cur.execute(
            '''
        INSERT INTO summary (note_id, note_created_at, note_received_at, diff, instance_name, instance_host, instance_softwareName, instance_softwareVersion, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (note_id, note_created_at, note_received_at, diff, instance_name,
              instance_host, instance_softwareName, instance_softwareVersion))
        conn.commit()
    except Exception as e:
        logger.error(f"Error: {e}")
        pass
    else:
        logger.info(f"Summary {note_id} inserted.")


def insert_error(note_id, note_created_at, note_received_at, error):
    try:
        logger.error(f"Inserting error: {note_id}")
        cur.execute(
            '''
        INSERT INTO error (note_id, note_created_at, note_received_at, error, created_at) VALUES (?, ?, ?, ?, datetime('now'))
        ''', (note_id, note_created_at, note_received_at, error))
        conn.commit()
    except Exception as e:
        logger.error(f"Error: {e}")
        pass
    else:
        logger.info(f"Error {note_id} inserted.")


def get_avg_diff(start_datetime, end_datetime):
    try:
        logger.info(
            f"Getting average diff for datetime range: {start_datetime} - {end_datetime}"
        )
        cur.execute(
            '''
        SELECT instance_name, instance_host, instance_softwareName, instance_softwareVersion, AVG(diff)
        FROM summary
        WHERE created_at BETWEEN ? AND ?
        GROUP BY instance_name, instance_host, instance_softwareName, instance_softwareVersion
        ''', (start_datetime, end_datetime))
        res = cur.fetchall()
    except Exception as e:
        logger.error(f"Error: {e}")
        pass
    else:
        logger.info(
            f"Average diff got for datetime range: {start_datetime} - {end_datetime}"
        )
        return res
