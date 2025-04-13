# Career Advisor Application

A Django application that provides career advice, job recommendations, and GitHub user matching based on skills.

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add the following variables:
     ```
     GITHUB_TOKEN=your-github-token-here
     ```
   - Generate a GitHub token at https://github.com/settings/tokens with the following scopes:
     - `read:user`
     - `user:email`
     - `read:org`

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Start the development server:
   ```
   python manage.py runserver
   ```

## Features

- Career advice based on user profile
- Job recommendations from LinkedIn
- GitHub user matching based on skills
- Resume feedback
- Dynamic quiz generation
- AI-powered insights

## Performance Optimization

The GitHub user matching feature has been optimized for speed:
- Uses async/await for parallel API requests
- Implements caching to reduce API calls
- Processes users in batches
- Limits the number of API calls per request

## Environment Variables

The following environment variables are required:

- `GITHUB_TOKEN`: Your GitHub API token for accessing the GitHub API

## License

MIT 