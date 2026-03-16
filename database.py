import sqlite3
  from typing import List, Dict, Optional
  from contextlib import contextmanager
  import os

  DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'jobs.db')


  class DatabaseManager:
      def __init__(self, db_path: str = DATABASE_PATH):
          self.db_path = db_path
          self._init_db()

      @contextmanager
      def _get_connection(self):
          conn = sqlite3.connect(self.db_path)
          conn.row_factory = sqlite3.Row
          try:
              yield conn
              conn.commit()
          except Exception:
              conn.rollback()
              raise
          finally:
              conn.close()

      def _init_db(self):
          with self._get_connection() as conn:
              cursor = conn.cursor()
              cursor.execute('''
                  CREATE TABLE IF NOT EXISTS jobs (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id TEXT NOT NULL,
                      status TEXT DEFAULT 'To Apply',
                      department TEXT,
                      company TEXT,
                      title TEXT,
                      url TEXT,
                      duration TEXT,
                      location TEXT,
                      open_date TEXT,
                      apply_date TEXT,
                      channel TEXT,
                      portfolio TEXT DEFAULT 'No',
                      notes TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                  )
              ''')
              cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON jobs(user_id)')

      def get_all_jobs(self, user_id: str) -> List[Dict]:
          with self._get_connection() as conn:
              cursor = conn.cursor()
              cursor.execute('''
                  SELECT id, status, department, company, title, url, duration,
                         location, open_date, apply_date, channel, portfolio, notes
                  FROM jobs WHERE user_id = ? ORDER BY created_at DESC
              ''', (user_id,))
              return [{
                  'id': row['id'], 'Status': row['status'], 'Department': row['department'] or '',
                  'Company': row['company'] or '', 'Title': row['title'] or '', 'URL': row['url'] or '',
                  'Duration': row['duration'] or '', 'Location': row['location'] or '',
                  'Open Date': row['open_date'] or '', 'Apply Date': row['apply_date'] or '',
                  'Channel': row['channel'] or '', 'Portfolio': row['portfolio'] or 'No',
                  'Notes': row['notes'] or ''
              } for row in cursor.fetchall()]

      def add_job(self, user_id: str, job_data: Dict) -> Optional[int]:
          if self.url_exists(user_id, job_data.get('url', '')):
              return None
          with self._get_connection() as conn:
              cursor = conn.cursor()
              cursor.execute('''
                  INSERT INTO jobs (user_id, status, department, company, title, url,
                                    duration, location, open_date, apply_date, channel, portfolio, notes)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              ''', (user_id, job_data.get('status', 'To Apply'), job_data.get('department', ''),
                    job_data.get('company', ''), job_data.get('title', ''), job_data.get('url', ''),
                    job_data.get('duration', ''), job_data.get('location', ''), job_data.get('open_date', ''),
                    job_data.get('apply_date', ''), job_data.get('channel', ''),
                    job_data.get('portfolio', 'No'), job_data.get('notes', '')))
              return cursor.lastrowid

      def url_exists(self, user_id: str, url: str) -> bool:
          if not url:
              return False
          with self._get_connection() as conn:
              cursor = conn.cursor()
              cursor.execute('SELECT 1 FROM jobs WHERE user_id = ? AND url = ?', (user_id, url))
              return cursor.fetchone() is not None

      def update_status(self, job_id: int, user_id: str, new_status: str) -> bool:
          with self._get_connection() as conn:
              cursor = conn.cursor()
              cursor.execute('UPDATE jobs SET status = ? WHERE id = ? AND user_id = ?', (new_status, job_id,
  user_id))
              return cursor.rowcount > 0

      def update_field(self, job_id: int, user_id: str, field: str, value: str) -> bool:
          field_map = {'status': 'status', 'department': 'department', 'company': 'company', 'title': 'title',
                       'url': 'url', 'duration': 'duration', 'location': 'location', 'open_date': 'open_date',
                       'apply_date': 'apply_date', 'channel': 'channel', 'portfolio': 'portfolio', 'notes': 'notes'}
          column = field_map.get(field.lower())
          if not column:
              return False
          with self._get_connection() as conn:
              cursor = conn.cursor()
              cursor.execute(f'UPDATE jobs SET {column} = ? WHERE id = ? AND user_id = ?', (value, job_id, user_id))
              return cursor.rowcount > 0

      def delete_job(self, job_id: int, user_id: str) -> bool:
          with self._get_connection() as conn:
              cursor = conn.cursor()
              cursor.execute('DELETE FROM jobs WHERE id = ? AND user_id = ?', (job_id, user_id))
              return cursor.rowcount > 0
