import aiohttp
import asyncio
from django.conf import settings
import logging
from functools import lru_cache
from datetime import datetime, timedelta
import json
from django.core.cache import cache
import os

logger = logging.getLogger(__name__)

# Cache GitHub API responses for 1 hour
CACHE_TIMEOUT = 3600  # 1 hour in seconds

# Get GitHub token from environment or settings
def get_github_token():
    # First try to get from environment
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        return token
    
    # Fall back to settings
    token = getattr(settings, 'GITHUB_TOKEN', '')
    if not token:
        logger.warning("GitHub token not found in environment or settings")
    return token

async def fetch_github_data(session, url, headers):
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            logger.error(f"GitHub API error: {response.status} for {url}")
            return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None

async def get_user_repos(session, repos_url, headers):
    cache_key = f"github_repos_{repos_url}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    data = await fetch_github_data(session, repos_url, headers)
    if data:
        cache.set(cache_key, json.dumps(data), CACHE_TIMEOUT)
    return data

async def get_user_details(session, user_url, headers):
    cache_key = f"github_user_{user_url}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    data = await fetch_github_data(session, user_url, headers)
    if data:
        cache.set(cache_key, json.dumps(data), CACHE_TIMEOUT)
    return data

async def process_github_user(session, user_info, user_skills_set, headers):
    if not user_info or 'login' not in user_info:
        return None

    # Get user details and repos in parallel
    user_details, repos = await asyncio.gather(
        get_user_details(session, user_info['url'], headers),
        get_user_repos(session, user_info['repos_url'], headers) if 'repos_url' in user_info else None
    )

    if not user_details:
        return None

    # Extract languages from repos
    languages = set()
    if repos:
        for repo in repos[:10]:  # Limit to top 10 repos for performance
            lang = repo.get('language')
            if lang:
                languages.add(lang.lower())

    # Find common skills
    common_skills = list(user_skills_set & languages)
    if not common_skills:
        return None

    return {
        'login': user_details['login'],
        'html_url': user_details['html_url'],
        'public_repos': user_details.get('public_repos', 0),
        'followers': user_details.get('followers', 0),
        'location': user_details.get('location'),
        'bio': user_details.get('bio'),
        'avatar_url': user_details.get('avatar_url'),
        'common_skills': common_skills,
    }

async def find_similar_github_users_async(user_skills, max_users=10):
    github_token = get_github_token()
    if not github_token:
        logger.error("GitHub token is not set")
        return []

    # Convert user skills to lowercase set for consistent comparison
    user_skills_set = set(skill.strip().lower() for skill in user_skills)
    logger.info(f"Looking for GitHub users with skills: {user_skills_set}")
    
    headers = {'Authorization': f'token {github_token}'}
    all_users = []
    seen_users = set()

    # Create connection pool with limits
    conn = aiohttp.TCPConnector(limit=10)
    timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout

    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        for skill in user_skills:
            # Search in both bio and language
            queries = [
                f"{skill} in:bio",
                f"language:{skill}"
            ]
            
            for query in queries:
                url = f"https://api.github.com/search/users?q={query}&per_page=10"
                cache_key = f"github_search_{query}"
                cached_data = cache.get(cache_key)
                
                if cached_data:
                    items = json.loads(cached_data)
                else:
                    data = await fetch_github_data(session, url, headers)
                    items = data.get('items', []) if data else []
                    cache.set(cache_key, json.dumps(items), CACHE_TIMEOUT)

                # Process users in parallel
                tasks = []
                for item in items:
                    if item['login'] not in seen_users:
                        seen_users.add(item['login'])
                        tasks.append(process_github_user(session, item, user_skills_set, headers))
                
                if tasks:
                    results = await asyncio.gather(*tasks)
                    all_users.extend([r for r in results if r])

                if len(all_users) >= max_users * 2:  # Get more than needed for sorting
                    break

            if len(all_users) >= max_users * 2:
                break

    # Sort by followers and common skills, then take top N
    sorted_users = sorted(
        all_users,
        key=lambda x: (len(x['common_skills']), x['followers']),
        reverse=True
    )[:max_users]

    logger.info(f"Returning {len(sorted_users)} unique GitHub matches")
    return sorted_users

def find_similar_github_users(user_skills, max_users=10):
    """
    Synchronous wrapper for the async function
    """
    return asyncio.run(find_similar_github_users_async(user_skills, max_users))
