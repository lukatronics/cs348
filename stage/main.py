import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime

def connect():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password=st.secrets['MYSQL_PASSWORD'],
        database='stage2'
    )

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

def add_meeting_ui():
    st.header('Add Meeting')
    title = st.text_input('Title')
    date = st.date_input('Date')
    start_time = st.time_input('Start Time')
    end_time = st.time_input('End Time')
    
    # get room data and add to dropdown menu
    rooms = get_rooms()
    room_options = {room_name: room_id for room_id, room_name in rooms}
    selected_room_name = st.selectbox('Select Room', list(room_options.keys()))
    room_id = room_options[selected_room_name]
    
    # get club data and add to dropdown menu
    clubs = get_clubs()
    club_options = {club_name: club_id for club_id, club_name in clubs}
    selected_club_name = st.selectbox('Select Club', list(club_options.keys()))
    club_id = club_options[selected_club_name]
    
    if st.button('Add Meeting'):
        meeting_data = (
            title,
            date.strftime('%Y-%m-%d'),
            start_time.strftime('%H:%M:%S'),
            end_time.strftime('%H:%M:%S'),
            int(room_id),
            int(club_id)
        )
        conn = connect()
        cursor = conn.cursor()

        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")

        try:
            add_meeting(cursor, meeting_data)
            conn.commit()
            st.success('Meeting added successfully!')
        except Exception as e:
            conn.rollback()
            st.error(f'Failed to Add Meeting, Try Again\n error {e}')
        finally:
            cursor.close()
            conn.close()

def edit_meeting_ui():
    st.header('Edit Meeting')

    # get meeting and ready to display
    meetings = get_meetings()
    if not meetings:
        st.warning('No meetings available to edit.')
        return

    meeting_options = {f"{title} (ID: {meeting_id})": meeting_id for meeting_id, title in meetings}
    selected_meeting_title = st.selectbox('Select Meeting to Edit', list(meeting_options.keys()))
    meeting_id = meeting_options[selected_meeting_title]

    # get meeting details
    meeting_details = get_meeting_details(meeting_id)
    if meeting_details:
        title, date, start_time, end_time, room_id, club_id = meeting_details

        # Convert start_time and end_time to datetime.time
        from datetime import datetime, timedelta

        if isinstance(start_time, timedelta):
            start_time_converted = (datetime.min + start_time).time()
        else:
            start_time_converted = start_time

        if isinstance(end_time, timedelta):
            end_time_converted = (datetime.min + end_time).time()
        else:
            end_time_converted = end_time

        # fill input data with previous data
        new_title = st.text_input('Title', value=title)
        new_date = st.date_input('Date', value=date)
        new_start_time = st.time_input('Start Time', value=start_time_converted)
        new_end_time = st.time_input('End Time', value=end_time_converted)

        # get room data and add to dropdown menu
        rooms = get_rooms()
        room_options = {room_name: room_id for room_id, room_name in rooms}
        room_name = next((name for name, id in room_options.items() if id == room_id), None)
        if room_name is None:
            selected_room_name = st.selectbox('Select Room', list(room_options.keys()))
        else:
            selected_room_name = st.selectbox('Select Room', list(room_options.keys()), index=list(room_options.keys()).index(room_name))
        new_room_id = room_options[selected_room_name]

        # get club data and add to dropdown menu
        clubs = get_clubs()
        club_options = {club_name: club_id for club_id, club_name in clubs}
        club_name = next((name for name, id in club_options.items() if id == club_id), None)
        if club_name is None:
            selected_club_name = st.selectbox('Select Club', list(club_options.keys()))
        else:
            selected_club_name = st.selectbox('Select Club', list(club_options.keys()), index=list(club_options.keys()).index(club_name))
        new_club_id = club_options[selected_club_name]

        if st.button('Update Meeting'):
            meeting_data = (
                new_title,
                new_date.strftime('%Y-%m-%d'),
                new_start_time.strftime('%H:%M:%S'),
                new_end_time.strftime('%H:%M:%S'),
                int(new_room_id),
                int(new_club_id)
            )
            conn = connect()
            cursor = conn.cursor()

            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")

            try:
                edit_meeting(cursor, int(meeting_id), meeting_data)
                conn.commit()
                st.success('Meeting updated successfully!')
            except Exception as e:
                conn.rollback()
                st.error(f"Failed to Update Meeting, Try Again\n Error: {e}")
            finally:
                cursor.close()
                conn.close()
    else:
        st.error('Meeting not found.')

def delete_meeting_ui():
    st.header('Delete Meeting')

    # get meeting data and add to dropdown menu
    meetings = get_meetings()
    if not meetings:
        st.warning('No meetings available to delete.')
        return

    meeting_options = {f"{title} (ID: {meeting_id})": meeting_id for meeting_id, title in meetings}
    selected_meeting_title = st.selectbox('Select Meeting to Delete', list(meeting_options.keys()))
    meeting_id = meeting_options[selected_meeting_title]

    if st.button('Delete Meeting'):
        conn = connect()
        cursor = conn.cursor()

        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")

        try:
            delete_meeting(cursor, int(meeting_id))
            conn.commit()
            st.success('Meeting deleted successfully!')
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to Delete Meeting, Try Again\n Error: {e}")
        finally:
            cursor.close()
            conn.close()

def generate_report_ui():
    st.header('Generate Meeting Report')
    start_date = st.date_input('Start Date', datetime.now())
    end_date = st.date_input('End Date', datetime.now())
    
    # get club data and add to dropdown menu
    clubs = get_clubs()
    club_options = {'All Clubs': None}
    club_options.update({club_name: club_id for club_id, club_name in clubs})
    selected_club_name = st.selectbox('Select Club', list(club_options.keys()))
    club_id = club_options[selected_club_name]

    # get room data and add to dropdown menu
    rooms = get_rooms()
    room_options = {'All Rooms': None}
    room_options.update({room_name: room_id for room_id, room_name in rooms})
    selected_room_name = st.selectbox('Select Room', list(room_options.keys()))
    room_id = room_options[selected_room_name]

    if st.button('Generate Report'):
        conn = connect()
        cursor = conn.cursor()
        
        # get report from server within time range
        report_data = generate_report(
            cursor,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            club_id,
            room_id
        )
        cursor.close()
        conn.close()

        if report_data:
            df = pd.DataFrame(report_data, columns=[
                'Meeting ID', 'Title', 'Date', 'Start Time', 'End Time', 'Club Name', 'Room Name'
            ])

            df['Start Time'] = df['Start Time'].apply(format_24h)
            df['End Time'] = df['End Time'].apply(format_24h)

            st.dataframe(df)

            durations = []
            for row in report_data:
                start_time = datetime.strptime(str(row[3]), '%H:%M:%S')
                end_time = datetime.strptime(str(row[4]), '%H:%M:%S')
                duration = (end_time - start_time).total_seconds() / 60 
                durations.append(duration)

            if durations:
                avg_duration = sum(durations) / len(durations)
                st.write(f'Average Duration: {avg_duration:.2f} minutes')
            else:
                st.write('No durations to calculate statistics.')
        else:
            st.write('No meetings found for the selected criteria.')

def format_24h(td):
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"

def get_rooms():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT room_id, room_name FROM Rooms")
    rooms = cursor.fetchall()
    cursor.close()
    conn.close()
    return rooms

def get_clubs():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT club_id, club_name FROM Clubs")
    clubs = cursor.fetchall()
    cursor.close()
    conn.close()
    return clubs

def get_meetings():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT meeting_id, title FROM Meetings")
    meetings = cursor.fetchall()
    cursor.close()
    conn.close()
    return meetings

def get_meeting_details(meeting_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, date, start_time, end_time, room_id, club_id
        FROM Meetings
        WHERE meeting_id = %s
    """, (meeting_id,))
    meeting = cursor.fetchone()
    cursor.close()
    conn.close()
    return meeting

def main():
    st.title('CS348 Stage 2')

    menu = ['Add Meeting', 'Edit Meeting', 'Delete Meeting', 'Generate Report']
    choice = st.sidebar.selectbox('Menu', menu)

    if choice == 'Add Meeting':
        add_meeting_ui()
    elif choice == 'Edit Meeting':
        edit_meeting_ui()
    elif choice == 'Delete Meeting':
        delete_meeting_ui()
    elif choice == 'Generate Report':
        generate_report_ui()

if __name__ == '__main__':
    main()