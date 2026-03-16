import os
  from dotenv import load_dotenv

  load_dotenv()

  DATABASE_PATH = os.getenv('DATABASE_PATH', 'jobs.db')
  SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production-to-a-random-string')

  SHEET_HEADERS = [
      'Status', 'Department', 'Company', 'Title', 'URL', 'Duration',
      'Location', 'Open Date', 'Apply Date', 'Channel', 'Portfolio', 'Notes'
  ]

  STATUS_OPTIONS = ['To Apply', 'Applied', 'Interviewing', 'Accepted', 'Rejected', 'Expired']
  CHANNEL_OPTIONS = ['Company Website', 'LinkedIn Easy Apply', 'LinkedIn', 'Email', 'Referral', 'Other']
