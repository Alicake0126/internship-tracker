import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime


class JobScraper:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def scrape(self, url: str) -> dict:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        if 'linkedin.com' in domain:
            return self._scrape_linkedin(url)
        elif 'lvmh.com' in domain:
            return self._scrape_lvmh(url)
        elif 'myworkdayjobs.com' in domain:
            return self._scrape_workday(url)
        elif 'ashbyhq.com' in domain:
            return self._scrape_ashby(url)
        elif 'greenhouse.io' in domain or 'boards.greenhouse' in domain:
            return self._scrape_greenhouse(url)
        else:
            return self._scrape_generic(url)

    def _scrape_linkedin(self, url: str) -> dict:
        result = self._get_default_result(url)
        result['channel'] = 'LinkedIn'
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')
            title_elem = soup.select_one('h1.top-card-layout__title, h1.topcard__title')
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
            company_elem = soup.select_one('a.topcard__org-name-link, .topcard__flavor--black-link')
            if company_elem:
                result['company'] = company_elem.get_text(strip=True)
            location_elem = soup.select_one('.topcard__flavor--bullet')
            if location_elem:
                result['location'] = location_elem.get_text(strip=True)
        except Exception as e:
            result['notes'] = f'Error: {str(e)}'
        return result

    def _scrape_lvmh(self, url: str) -> dict:
        result = self._get_default_result(url)
        result['channel'] = 'Company Website'
        brand_map = {'FRED': 'FRED', 'DIO': 'Dior', 'LV': 'Louis Vuitton', 'BVLG': 'Bulgari',
                     'TIF': 'Tiffany & Co.', 'GIV': 'Givenchy', 'KEN': 'Kenzo', 'FEN': 'Fendi',
                     'SEP': 'Sephora', 'GUE': 'Guerlain', 'LOE': 'Loewe', 'CEL': 'Celine'}
        job_id_match = re.search(r'/([A-Z]+)\d+', url)
        if job_id_match:
            result['company'] = brand_map.get(job_id_match.group(1), job_id_match.group(1))
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')
            title_elem = soup.select_one('h1')
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
            page_text = soup.get_text()
            loc_match = re.search(r'(Paris|London|New York|Tokyo|Milan|Singapore)', page_text, re.IGNORECASE)
            if loc_match:
                result['location'] = loc_match.group(1)
            duration_match = re.search(r'(\d+)\s*(?:months?|mois)', page_text, re.IGNORECASE)
            if duration_match:
                result['duration'] = f"{duration_match.group(1)} months"
        except Exception as e:
            result['notes'] = f'Error: {str(e)}'
        return result

    def _scrape_workday(self, url: str) -> dict:
        result = self._get_default_result(url)
        result['channel'] = 'Company Website'
        parsed = urlparse(url)
        subdomain = parsed.netloc.split('.')[0].lower()
        workday_companies = {'cc': 'Chanel', 'richemont': 'Richemont', 'cartier': 'Cartier', 'lvmh': 'LVMH'}
        result['company'] = workday_companies.get(subdomain, subdomain.title())
        try:
            path_match = re.search(r'(?:/en-[A-Z]{2})?/([^/]+)/job/(.+?)(?:/apply)?(?:\?|$)', url)
            if path_match:
                company_path, job_path = path_match.group(1), path_match.group(2)
                api_url = f"https://{parsed.netloc}/wday/cxs/{subdomain}/{company_path}/job/{job_path}"
                response = self.session.get(api_url, headers={'Accept': 'application/json'}, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    job_info = data.get('jobPostingInfo', {})
                    if job_info.get('title'):
                        result['title'] = job_info.get('title')
                    description = job_info.get('jobDescription', '')
                    brands = [('Van Cleef', 'Van Cleef & Arpels'), ('Cartier', 'Cartier'), ('Chanel', 'Chanel'),
                              ('Piaget', 'Piaget'), ('Montblanc', 'Montblanc')]
                    for pattern, name in brands:
                        if pattern.lower() in description.lower():
                            result['company'] = name
                            break
                    loc_match = re.search(r'(Paris|London|Geneva|Milan|New York)', description, re.IGNORECASE)
                    if loc_match:
                        result['location'] = loc_match.group(1)
        except Exception:
            url_match = re.search(r'/job/([^_]+)_', url)
            if url_match:
                result['title'] = url_match.group(1).replace('---', ' - ').replace('-', ' ')
        return result

    def _scrape_ashby(self, url: str) -> dict:
        result = self._get_default_result(url)
        result['channel'] = 'Company Website'
        company_match = re.search(r'ashbyhq\.com/([^/]+)', url)
        if company_match:
            result['company'] = company_match.group(1).replace('-', ' ').title()
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')
            title_elem = soup.select_one('title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                if ' - ' in title_text:
                    parts = title_text.split(' - ')
                    result['title'] = parts[0].strip()
                    if len(parts) > 1:
                        result['company'] = parts[1].strip()
            page_text = soup.get_text()
            loc_match = re.search(r'(Paris|London|New York|Milan)', page_text, re.IGNORECASE)
            if loc_match:
                result['location'] = loc_match.group(1)
        except Exception as e:
            result['notes'] = f'Error: {str(e)}'
        return result

    def _scrape_greenhouse(self, url: str) -> dict:
        result = self._get_default_result(url)
        result['channel'] = 'Company Website'
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')
            title_elem = soup.select_one('h1, .job-title')
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
            company_elem = soup.select_one('.company-name, [class*="company"]')
            if company_elem:
                result['company'] = company_elem.get_text(strip=True)
            location_elem = soup.select_one('.location, [class*="location"]')
            if location_elem:
                result['location'] = location_elem.get_text(strip=True)
        except Exception as e:
            result['notes'] = f'Error: {str(e)}'
        return result

    def _scrape_generic(self, url: str) -> dict:
        result = self._get_default_result(url)
        result['channel'] = 'Company Website'
        parsed = urlparse(url)
        domain_parts = parsed.netloc.replace('www.', '').split('.')
        if domain_parts:
            result['company'] = domain_parts[0].title()
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')
            for selector in ['h1', '[class*="job-title"]', '[class*="position-title"]', 'title']:
                elem = soup.select_one(selector)
                if elem and len(elem.get_text(strip=True)) > 3:
                    result['title'] = elem.get_text(strip=True)[:100]
                    break
            page_text = soup.get_text()
            loc_match = re.search(r'(Paris|London|New York|Berlin|Tokyo|Singapore|Amsterdam)', page_text,
re.IGNORECASE)
            if loc_match:
                result['location'] = loc_match.group(1)
            duration_match = re.search(r'(\d+)\s*(?:months?|mois|weeks?)', page_text, re.IGNORECASE)
            if duration_match:
                result['duration'] = duration_match.group(0)
            if re.search(r'portfolio', page_text, re.IGNORECASE):
                result['portfolio'] = 'Yes'
        except Exception as e:
            result['notes'] = f'Error: {str(e)}'
        return result

    def _get_default_result(self, url: str) -> dict:
        return {
            'status': 'To Apply', 'department': '', 'company': '', 'title': '', 'url': url,
            'duration': '', 'location': '', 'open_date': datetime.now().strftime('%Y-%m-%d'),
            'apply_date': '', 'channel': '', 'portfolio': 'No', 'notes': ''
        }
