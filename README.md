# Student Payment & Attendance Check-In System

A web-based application for tracking student payments and attendance using QR codes. Runs on Raspberry Pi, accessible via local Wi-Fi.

## Features

- 📱 **Mobile-Friendly**: Works on phones as PWA (Add to Home Screen)
- 📷 **QR Code Scanning**: In-browser scanning using phone camera
- 💰 **Payment Tracking**: Daily payments with tabs (pay later) support
- � **Record Modification**: Modify payment records for the same day (courses, payment status)
- �📊 **Attendance Tracking**: Automatic absent marking
- 📈 **Reports & Charts**: Daily and monthly reports with Chart.js
- 👥 **User Roles**: Admin (full access) and Staff (scan only)

## Default Users

| Username | Password  | Role  |
|----------|-----------|-------|
| admin    | admin123  | Admin |
| staff    | staff123  | Staff |

**⚠️ Change passwords immediately after first login!**

## Record Modification Feature

When scanning or selecting a student who already has a payment record for today, the system automatically displays the existing record instead of creating a duplicate entry. This allows you to:

- **Modify Courses**: Change which courses the student is paying for
- **Update Payment Status**: Switch between immediate payment and tabs (pay later)
- **Keep Changes**: Record will update with new selections automatically

The system shows a yellow modal with the existing record details and allows you to make changes before saving. This prevents duplicate daily records and makes it easy to correct mistakes without manual deletion.

## Installation

### 1. Clone or download the project
```bash
cd student_checkin