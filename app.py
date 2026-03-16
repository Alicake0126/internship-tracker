from flask import Flask, render_template, request, jsonify, session
  from scraper import JobScraper
  from database import DatabaseManager
  from config import STATUS_OPTIONS, CHANNEL_OPTIONS, SECRET_KEY
  from uuid import uuid4

  app = Flask(__name__)
  app.secret_key = SECRET_KEY
  scraper = JobScraper()
  db = DatabaseManager()

  @app.before_request
  def ensure_user_id():
      if 'user_id' not in session:
          session['user_id'] = str(uuid4())
          session.permanent = True

  @app.route('/')
  def index():
      return render_template('index.html', status_options=STATUS_OPTIONS, channel_options=CHANNEL_OPTIONS)

  @app.route('/api/jobs', methods=['GET'])
  def get_jobs():
      try:
          return jsonify({'success': True, 'jobs': db.get_all_jobs(session.get('user_id'))})
      except Exception as e:
          return jsonify({'success': False, 'error': str(e)}), 500

  @app.route('/api/jobs', methods=['POST'])
  def add_job():
      try:
          url = request.get_json().get('url', '').strip()
          if not url:
              return jsonify({'success': False, 'error': 'Please provide a job URL'}), 400
          user_id = session.get('user_id')
          if db.url_exists(user_id, url):
              return jsonify({'success': False, 'error': 'This job URL already exists'}), 400
          job_data = scraper.scrape(url)
          job_id = db.add_job(user_id, job_data)
          if job_id:
              job_data['id'] = job_id
              return jsonify({'success': True, 'job': job_data})
          return jsonify({'success': False, 'error': 'This job URL already exists'}), 400
      except Exception as e:
          return jsonify({'success': False, 'error': str(e)}), 500

  @app.route('/api/jobs/<int:job_id>/status', methods=['PATCH'])
  def update_status(job_id):
      try:
          new_status = request.get_json().get('status')
          if not new_status:
              return jsonify({'success': False, 'error': 'Please provide a new status'}), 400
          if db.update_status(job_id, session.get('user_id'), new_status):
              return jsonify({'success': True})
          return jsonify({'success': False, 'error': 'Update failed'}), 500
      except Exception as e:
          return jsonify({'success': False, 'error': str(e)}), 500

  @app.route('/api/jobs/<int:job_id>/field', methods=['PATCH'])
  def update_field(job_id):
      try:
          data = request.get_json()
          field, value = data.get('field'), data.get('value', '')
          if not field:
              return jsonify({'success': False, 'error': 'Please provide a field name'}), 400
          if db.update_field(job_id, session.get('user_id'), field, value):
              return jsonify({'success': True})
          return jsonify({'success': False, 'error': 'Update failed'}), 500
      except Exception as e:
          return jsonify({'success': False, 'error': str(e)}), 500

  @app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
  def delete_job(job_id):
      try:
          if db.delete_job(job_id, session.get('user_id')):
              return jsonify({'success': True})
          return jsonify({'success': False, 'error': 'Delete failed'}), 500
      except Exception as e:
          return jsonify({'success': False, 'error': str(e)}), 500

  if __name__ == '__main__':
      app.run(debug=True, port=5000)
