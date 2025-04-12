import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def find_similar_github_users(user_skills, max_users=10):
    if not settings.GITHUB_TOKEN:
        logger.error("GitHub token is not set")
        return []

    headers = {'Authorization': f'token {settings.GITHUB_TOKEN}'}
    all_users = []

    for skill in user_skills:
        query = f"{skill} in:bio"
        url = f"https://api.github.com/search/users?q={query}&per_page=10"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            if response.status_code == 200:
                for item in response.json().get('items', []):
                    try:
                        user_data = requests.get(item['url'], headers=headers)
                        user_data.raise_for_status()
                        user_info = user_data.json()
                        
                        if 'login' in user_info:
                            all_users.append({
                                'login': user_info['login'],
                                'html_url': user_info['html_url'],
                                'public_repos': user_info.get('public_repos', 0),
                                'followers': user_info.get('followers', 0),
                                'location': user_info.get('location'),
                                'bio': user_info.get('bio'),
                                'avatar_url': user_info.get('avatar_url'),
                            })
                    except requests.RequestException as e:
                        logger.error(f"Error fetching user details: {str(e)}")
                        continue
                        
        except requests.RequestException as e:
            logger.error(f"Error searching GitHub users for skill {skill}: {str(e)}")
            continue

    # Sort by followers and return top N
    sorted_users = sorted(all_users, key=lambda x: x['followers'], reverse=True)
    seen = set()
    unique_users = []
    for user in sorted_users:
        if user['login'] not in seen:
            seen.add(user['login'])
            unique_users.append(user)
        if len(unique_users) >= max_users:
            break

    return unique_users
