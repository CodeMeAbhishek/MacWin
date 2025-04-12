# scraper/utils.py
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import traceback

class JobScraper:
    def __init__(self):
        self.jobs_per_tech = 10
        self.all_jobs = []
        self.current_session = None
        self.last_search = None

    def reset_session(self, session_id):
        if self.current_session != session_id:
            self.current_session = session_id
            self.all_jobs = []
            self.last_search = None
            return True
        return False

    def is_new_search(self, technologies):
        if self.last_search is None:
            self.last_search = technologies
            return True
        last_terms = set(t.strip().lower() for t in self.last_search.split(','))
        new_terms = set(t.strip().lower() for t in technologies.split(','))
        if not last_terms.intersection(new_terms):
            self.last_search = technologies
            return True
        return False

    async def scrape_multiple_technologies(self, technologies, session_id):
        if self.reset_session(session_id) or self.is_new_search(technologies):
            self.all_jobs = []
        
        print(f"Starting job search for technologies: {technologies}")
        tech_list = [tech.strip() for tech in technologies.split(',')]
        print(f"Parsed technology list: {tech_list}")
        
        tasks = [self.scrape_single_technology(tech) for tech in tech_list if tech]
        if not tasks:
            print("No valid technologies to search for")
            return []
        try:
            await asyncio.gather(*tasks)
            print(f"Completed scraping. Found {len(self.all_jobs)} total jobs")
        except Exception as e:
            print("\u274c Error during scraping:", str(e))
            traceback.print_exc()
        return self.all_jobs

    async def scrape_single_technology(self, tech):
        url = f"https://www.linkedin.com/jobs/search/?keywords={tech}"
        print(f"Scraping jobs for {tech} from {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Referer': 'https://www.linkedin.com/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        print(f"⚠️ LinkedIn returned status {response.status} for {tech}")
                        return
                    content = await response.text()
                    print(f"Retrieved {len(content)} bytes of content for {tech}")
                    
                    if "JSESSIONID" not in response.cookies:
                        print(f"⚠️ LinkedIn may have blocked the request for {tech}")
                        return
                        
                    if "captcha" in content.lower() or "please verify you are a human" in content.lower():
                        print(f"⚠️ LinkedIn is requesting CAPTCHA verification for {tech}")
                        return
                        
                    jobs = self.parse_jobs(content, tech)
                    print(f"Found {len(jobs)} jobs for {tech}")
                    self.all_jobs.extend(jobs)
        except Exception as e:
            print(f"⚠️ Error scraping {tech}: {str(e)}")
            traceback.print_exc()

    def parse_jobs(self, content, tech):
        try:
            soup = BeautifulSoup(content, 'html.parser')
            job_cards = soup.find_all('div', class_='job-search-card')
            print(f"Found {len(job_cards)} job cards in HTML for {tech}")
            
            jobs = []
            for card in job_cards[:self.jobs_per_tech]:
                job_info = self.extract_job_info(card, tech)
                if job_info:
                    jobs.append(job_info)
            
            if not jobs:
                print(f"⚠️ Could not extract any valid job information from cards for {tech}")
            return jobs
        except Exception as e:
            print(f"⚠️ Error parsing jobs for {tech}: {str(e)}")
            traceback.print_exc()
            return []

    def extract_job_info(self, card, tech):
        try:
            title = card.find('h3', class_='base-search-card__title')
            company = card.find('h4', class_='base-search-card__subtitle')
            location = card.find('span', class_='job-search-card__location')
            link = card.find('a', class_='base-card__full-link')
            if not all([title, company, location, link]):
                return None
            return {
                'title': title.text.strip(),
                'company': company.text.strip(),
                'location': location.text.strip(),
                'link': link['href'],
                'technology': tech
            }
        except:
            return None
