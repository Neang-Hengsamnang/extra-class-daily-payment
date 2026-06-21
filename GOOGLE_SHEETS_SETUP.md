# Google Sheets Export Setup Guide

## Overview
The Export to Google Sheets function allows you to export monthly payment reports to Google Sheets with a professional multi-row header structure:
- **Row 1 Headers (Merged Cells)**: Student ID, Student Name, Student Gender, Student Grade, Month/Year (spanning all days), Total Revenue, Total Tabs
- **Row 2 Headers**: Day numbers (01, 02, 03, etc.) under each date column

## Prerequisites
1. A Google Cloud Project
2. Google Sheets API enabled
3. Service Account credentials
4. Python dependencies installed

## Setup Steps

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click the project dropdown at the top
4. Click "NEW PROJECT"
5. Enter a project name (e.g., "Payment System Export")
6. Click "CREATE"

### Step 2: Enable Google Sheets API

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for "Google Sheets API"
3. Click on it and then click "ENABLE"
4. Also search for and enable "Google Drive API"

### Step 3: Create Service Account

1. Go to "APIs & Services" > "Credentials"
2. Click "CREATE CREDENTIALS" > "Service Account"
3. Fill in the service account details:
   - Service account name: `payment-export-service`
   - Click "CREATE AND CONTINUE"
4. Click "CREATE KEY"
5. Choose "JSON"
6. Click "CREATE"
7. A JSON file will download automatically - **SAVE THIS FILE SECURELY**

### Step 4: Place Credentials File

1. Rename the downloaded JSON file to `credentials.json`
2. Place it in the root directory of your project:
   ```
   d:\Me\My Created System\Extraclass_Daily_Payment_System\credentials.json
   ```

### Step 5: Install Python Dependencies

Install the required packages:
```bash
pip install -r requirements.txt
```

This will install:
- `gspread` - Python client for Google Sheets API
- `google-auth-oauthlib` - Google OAuth2 authentication
- `google-auth-httplib2` - HTTP transport for Google Auth

## Usage

### From the Web Interface

1. Navigate to the Monthly Report page (Admin > Monthly Report)
2. Select the desired Year and Month
3. Click the "នាំយកទៅ Google Sheets" (Export to Google Sheets) button
4. A new Google Sheet will be created and automatically opened in your browser

### From API

You can also use the API endpoint directly:

```bash
curl -X POST http://localhost:5000/api/export-monthly-report \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2024,
    "month": 6,
    "spreadsheet_name": "Monthly_Payment_2024_06"
  }'
```

## Sheet Structure

The exported sheet contains:

### Headers (2 rows)
- **Row 1**: Column names with some spanning multiple cells
- **Row 2**: Day numbers (01-31) under the date columns

### Data Columns
1. **Student ID** - Student identifier (2-row merge)
2. **Student Name** - Full name of student (2-row merge)
3. **Student Gender** - Gender information (2-row merge)
4. **Student Grade** - Grade/class level (2-row merge)
5. **Daily Columns** - One column per day of the month showing payment amount
   - First row shows: `YYYY/MM`
   - Second row shows: `DD` (day number)
6. **Total Revenue** - Sum of all paid payments (2-row merge)
7. **Total Tabs** - Sum of all unpaid payments (2-row merge)

### Formatting
- Header rows have:
  - Bold text
  - Center alignment
  - Light gray background
- Data cells with amounts are formatted as currency (៛ Khmer Riel)
- Column widths are automatically adjusted

## Troubleshooting

### Error: "credentials.json not found"
- Make sure the credentials.json file is in the project root directory
- Check the file path: `d:\Me\My Created System\Extraclass_Daily_Payment_System\credentials.json`

### Error: "Authentication failed"
- Verify the credentials.json file content is valid JSON
- Check that the Google Cloud project has Sheets API enabled
- Ensure the service account has not been deleted

### Permission Denied Errors
- Check that the service account email has not been revoked
- Re-create the service account key if needed

### Sheet Not Opening
- Check your browser's popup blocker settings
- Try opening the URL manually from the success message

## Security Notes

⚠️ **Important**: Keep your `credentials.json` file secure:
- Never commit it to version control (add to .gitignore)
- Never share it publicly
- Only share Google Sheets URLs with intended recipients
- Consider using environment variables for production deployments

## Additional Features

The export automatically:
- ✅ Merges cells for multi-row headers
- ✅ Formats currency values
- ✅ Adjusts column widths for readability
- ✅ Creates a public readable link (optional)
- ✅ Only includes active students
- ✅ Calculates totals per student
- ✅ Displays empty cells for days with no payments

## Support

For issues with:
- **gspread library**: https://docs.gspread.org/
- **Google Sheets API**: https://developers.google.com/sheets
- **Google Authentication**: https://developers.google.com/identity/protocols/oauth2

