from django.shortcuts import render
import asyncio
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bs4 import BeautifulSoup
import aiohttp
from .models import Job
import csv
from datetime import datetime
import os
import json
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
        
        tech_list = [tech.strip() for tech in technologies.split(',')]
        tasks = []
        for tech in tech_list:
            if tech:  # Only create tasks for non-empty technologies
                tasks.append(self.scrape_single_technology(tech))
        
        if not tasks:
            return []
            
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            traceback.print_exc()
            raise
            
        return self.all_jobs

    async def scrape_single_technology(self, tech):
        url = f"https://www.linkedin.com/jobs/search/?keywords={tech}"
        try:
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Error fetching jobs for {tech}: Status {response.status}")
                        return
                    
                    print(f"Successfully fetched jobs for {tech}")
                    content = await response.text()
                    jobs = self.parse_jobs(content, tech)
                    if jobs:
                        print(f"Found {len(jobs)} jobs for {tech}")
                        self.all_jobs.extend(jobs)
                    else:
                        print(f"No jobs found for {tech}")
        except asyncio.TimeoutError:
            print(f"Timeout while scraping jobs for {tech}")
        except aiohttp.ClientError as e:
            print(f"Network error while scraping {tech}: {str(e)}")
        except Exception as e:
            print(f"Error scraping {tech}: {str(e)}")
            traceback.print_exc()

    def parse_jobs(self, content, tech):
        try:
            soup = BeautifulSoup(content, 'html.parser')
            job_cards = soup.find_all('div', class_='job-search-card')
            jobs = []
            
            for card in job_cards[:self.jobs_per_tech]:
                job_info = self.extract_job_info(card, tech)
                if job_info:
                    jobs.append(job_info)
            return jobs
        except Exception as e:
            print(f"Error parsing jobs for {tech}: {str(e)}")
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
        except Exception as e:
            print(f"Error extracting job info: {str(e)}")
            return None

def home(request):
    return render(request, 'scraper/home.html')

@csrf_exempt
@require_http_methods(["POST"])
async def search(request):
    print("Received search request")
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
            
        technologies = data.get('technologies', '').strip()
        session_id = data.get('sessionId', '')
        
        print(f"Technologies: {technologies}")
        print(f"Session ID: {session_id}")
        
        if not technologies:
            return JsonResponse({'error': 'No technologies provided'}, status=400)
        
        scraper = JobScraper()
        try:
            jobs = await scraper.scrape_multiple_technologies(technologies, session_id)
            
            if not jobs:
                return JsonResponse({'error': 'No jobs found'}, status=404)
            
            # Save jobs to database
            for job in jobs:
                try:
                    Job.objects.create(**job)
                except Exception as e:
                    print(f"Error saving job to database: {str(e)}")
            
            # Save to CSV
            try:
                save_to_csv(jobs, scraper.is_new_search(technologies))
            except Exception as e:
                print(f"Error saving to CSV: {str(e)}")
            
            return JsonResponse(jobs, safe=False)
        except Exception as e:
            print(f"Scraping error: {str(e)}")
            traceback.print_exc()
            return JsonResponse({'error': 'Error occurred while scraping jobs'}, status=500)
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

def save_to_csv(jobs, is_new_session):
    if not jobs:
        return
        
    filename = 'job_listings.csv'
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'company', 'location', 'link', 'technology'])
        if not file_exists or is_new_session:
            writer.writeheader()
        writer.writerows(jobs)
