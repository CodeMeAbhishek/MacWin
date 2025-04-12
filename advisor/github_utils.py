import requests
from django.conf import settings

def find_similar_github_users(user_skills, max_users=10):
    headers = {'Authorization': f'token {settings.GITHUB_TOKEN}'}
    all_users = []

    for skill in user_skills:
        query = f"{skill} in:bio"
        url = f"https://api.github.com/search/users?q={query}&per_page=10"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            for item in response.json().get('items', []):
                user_data = requests.get(item['url'], headers=headers).json()
                if 'login' in user_data:
                    all_users.append({
                        'login': user_data['login'],
                        'html_url': user_data['html_url'],
                        'public_repos': user_data.get('public_repos', 0),
                        'followers': user_data.get('followers', 0),
                        'location': user_data.get('location'),
                        'bio': user_data.get('bio'),
                        'avatar_url': user_data.get('avatar_url'),
                    })

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
