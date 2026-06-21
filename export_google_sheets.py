"""
Google Sheets export module for monthly payment reports.
Exports monthly payment data into dedicated monthly tabs with multi-row headers.
"""

import gspread
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
import os
from datetime import date, timedelta
from models import Student, Payment
from extensions import db
import calendar

GOOGLE_SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']


def get_google_sheets_client():
    """
    Authenticate and return gspread client.
    Expects credentials.json file in project root.
    """
    creds_file = os.path.join(os.path.dirname(__file__), 'credentials.json')
    
    if not os.path.exists(creds_file):
        raise FileNotFoundError(
            f"Google credentials file not found at {creds_file}. "
            "Please set up Google OAuth2 credentials. "
            "See: https://docs.gspread.org/en/latest/oauth2.html"
        )
    
    creds = Credentials.from_service_account_file(creds_file, scopes=GOOGLE_SHEETS_SCOPES)
    return gspread.authorize(creds)


def create_monthly_payment_sheet(year, month, spreadsheet_id=None):
    """
    Open an existing Google Sheet by ID and populate a specific monthly tab.
    
    Tab naming convention: YYYY-MM (e.g., "2026-06")
    """
    # Force your shared spreadsheet target ID
    spreadsheet_id = "1sUQ9UmjCxaZua2WRr5mP8oh1NjtsuAFlMbWD1CiXsUY"
    
    try:
        client = get_google_sheets_client()
    except FileNotFoundError as e:
        return {'error': str(e)}
    
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Define your new sheet tab name format
        sheet_name = f"{year}-{month:02d}" 
        
        try:
            # If the monthly tab already exists, open it and clear old records
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            # If the monthly tab does not exist, create it safely
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=50)
            
    except Exception as e:
        return {'error': f"Failed to access spreadsheet: {str(e)}. Ensure the ID is correct and shared with the service account email."}
    
    # Get database data
    active_students = Student.query.filter_by(is_active=True).order_by(Student.id).all()
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    payments = Payment.query.filter(
        Payment.date >= start_date,
        Payment.date < end_date
    ).all()
    
    payment_dict = {}
    for p in payments:
        key = (p.student_id, p.date)
        payment_dict[key] = p
    
    days_in_month = calendar.monthrange(year, month)[1]
    
    # ===== BUILD HEADERS =====
    header_row1 = ['Student ID', 'Student Name', 'Student Gender', 'Student Grade']
    header_row2 = ['', '', '', '']
    
    for day in range(1, days_in_month + 1):
        header_row1.append(f"{year}/{month:02d}")
        header_row2.append(f"{day:02d}")
    
    header_row1.extend(['Total Revenue', 'Total Tabs'])
    header_row2.extend(['', ''])
    
    # ===== BUILD DATA ROWS =====
    data_rows = []
    for student in active_students:
        row = [
            student.id,
            student.full_name,
            student.gender or '',
            student.grade_level or ''
        ]
        
        total_revenue = 0
        total_tabs = 0
        
        for day in range(1, days_in_month + 1):
            payment_date = date(year, month, day)
            payment = payment_dict.get((student.id, payment_date))
            
            if payment:
                row.append(payment.total_amount)
                if payment.is_paid:
                    total_revenue += payment.total_amount
                else:
                    total_tabs += payment.total_amount
            else:
                row.append('')
        
        row.extend([total_revenue, total_tabs])
        data_rows.append(row)
    
    # ===== WRITE TO WORKSHEET =====
    all_rows = [header_row1, header_row2] + data_rows
    
    # Resize worksheet dimensions dynamically to fit data exactly
    worksheet.resize(len(all_rows), len(header_row1))
    worksheet.append_rows(all_rows, value_input_option='RAW')
    
    # ===== FORMAT SHEET (BATCH UPDATE) =====
    requests = []
    sheet_id = worksheet._properties['sheetId']  # Captures the unique ID of our new tab
    
    # Merge cells for student info headers (columns index 0 to 3)
    for col in range(1, 5):
        requests.append({
            'mergeCells': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 2,
                    'startColumnIndex': col - 1,
                    'endColumnIndex': col
                },
                'mergeType': 'MERGE_ALL'
            }
        })
    
    # Merge month label row spanning across all day columns
    start_col = 5  
    end_col = start_col + days_in_month
    if days_in_month > 1:
        requests.append({
            'mergeCells': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': start_col - 1,
                    'endColumnIndex': end_col - 1
                },
                'mergeType': 'MERGE_ALL'
            }
        })
    
    # Merge final Summary total headers
    for col in range(end_col, end_col + 2):
        requests.append({
            'mergeCells': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 2,
                    'startColumnIndex': col - 1,
                    'endColumnIndex': col
                },
                'mergeType': 'MERGE_ALL'
            }
        })
    
    # Batch apply Header Styles to entire rows 1 & 2 at once (No individual loops)
    header_format = {
        'textFormat': {'bold': True},
        'horizontalAlignment': 'CENTER',
        'verticalAlignment': 'MIDDLE',
        'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85}
    }
    requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 0,
                'endRowIndex': 2,
                'startColumnIndex': 0,
                'endColumnIndex': len(header_row1)
            },
            'cell': {'userEnteredFormat': header_format},
            'fields': 'userEnteredFormat'
        }
    })
    
    # Batch apply Khmer Riel currency configurations to all dataset payment grids at once
    currency_format = {
        'numberFormat': {
            'type': 'CURRENCY',
            'pattern': '[$៛-044]#,##0'
        },
        'horizontalAlignment': 'RIGHT'
    }
    if data_rows:
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 2,
                    'endRowIndex': 2 + len(data_rows),
                    'startColumnIndex': 4,
                    'endColumnIndex': len(header_row1)
                },
                'cell': {'userEnteredFormat': currency_format},
                'fields': 'userEnteredFormat'
            }
        })
    
    # Run API styling batch compilation
    if requests:
        spreadsheet.batch_update({'requests': requests})
    
    # Execute column layout distributions
    set_column_widths(worksheet, days_in_month)
    
    return {
        'success': True,
        'spreadsheet_id': spreadsheet.id,
        'spreadsheet_url': f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit#gid={sheet_id}",
        'message': f"Monthly report for {year}/{month:02d} exported successfully to tab '{sheet_name}'."
    }


def set_column_widths(worksheet, days_in_month):
    """Set appropriate column widths relative to the active target sheet."""
    requests = []
    sheet_id = worksheet._properties['sheetId']  # Fixes global sheetId targeting bug
    
    column_widths = {
        0: 100,  # Student ID
        1: 150,  # Student Name
        2: 120,  # Student Gender
        3: 120,  # Student Grade
    }
    
    for col in range(4, 4 + days_in_month):
        column_widths[col] = 80
    
    column_widths[4 + days_in_month] = 120      # Total Revenue
    column_widths[4 + days_in_month + 1] = 100  # Total Tabs
    
    for col_idx, width in column_widths.items():
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': col_idx,
                    'endIndex': col_idx + 1
                },
                'properties': {
                    'pixelSize': width
                },
                'fields': 'pixelSize'
            }
        })
    
    if requests:
        worksheet.spreadsheet.batch_update({'requests': requests})