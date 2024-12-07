import mysql.connector
import streamlit as st

# import pydeck as pdk
# from streamlit_folium import folium_static
# import folium
# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi

def add_meeting(cursor, meeting_data):
    cursor.callproc('AddMeeting', meeting_data)

def edit_meeting(cursor, meeting_id, meeting_data):
    cursor.callproc('EditMeeting', (meeting_id,) + meeting_data)

def delete_meeting(cursor, meeting_id):
    cursor.callproc('DeleteMeeting', (meeting_id,))

def generate_report(cursor, start_date, end_date, club_id=None, room_id=None):
    cursor.callproc('GetMeetingReport', (start_date, end_date, club_id, room_id))
    results = []
    for result in cursor.stored_results():
        results.extend(result.fetchall())
    return results

def main():
    connect = mysql.connector.connect(
        host=st.secrets['HOST'],
        user=st.secrets['USER'],
        password=st.secrets['MYSQL_PASSWORD'],
        database=st.secrets['DATA']
    )
    cursor = connect.cursor(prepared=True)

    cursor.execute("SHOW INDEX FROM Meetings WHERE Key_name='idx_meetings_date_club_room'")
    if not cursor.fetchone():
        cursor.execute("CREATE INDEX idx_meetings_date_club_room ON Meetings(date, club_id, room_id)")

    init_rooms = [
        ('WALC 1013', 50),
        ('KRAN 3001', 30),
        ('HAAS B013', 20)
    ]

    cursor.executemany("""
        INSERT INTO Rooms (room_name, capacity)
        VALUES (%s, %s)
    """, init_rooms)

    init_clubs = [
        ('Robotics Club', 'A club for humanoid robot enthusiasts.'),
        ('Music Club', 'A club for music lovers (any genre).'),
        ('Movie Club', 'A club for movie lovers (any genre).')
    ]

    cursor.executemany("""
        INSERT INTO Clubs (club_name, description)
        VALUES (%s, %s)
    """, init_clubs)
    
    init_meeting = (
        'General Meeting for Robotics Club',
        '2024-10-29',
        '10:00:00',
        '11:00:00',
        1,
        1   
    )

    cursor.execute("""
        INSERT INTO Meetings (title, date, start_time, end_time, room_id, club_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, init_meeting)

    connect.commit()
    cursor.close()
    connect.close()

if __name__ == '__main__':
    main()