"""Test script for all API endpoints."""
import requests

base = 'http://127.0.0.1:8000'

# Test frontend serving
r = requests.get(f'{base}/')
print(f'GET / : {r.status_code}, has CineMatch: {"CineMatch" in r.text}')

r = requests.get(f'{base}/dashboard')
print(f'GET /dashboard : {r.status_code}, has CineMatch: {"CineMatch" in r.text}')

r = requests.get(f'{base}/static/css/style.css')
print(f'GET /static/css/style.css : {r.status_code}, length: {len(r.text)}')

r = requests.get(f'{base}/static/js/auth.js')
print(f'GET /static/js/auth.js : {r.status_code}, length: {len(r.text)}')

r = requests.get(f'{base}/static/js/app.js')
print(f'GET /static/js/app.js : {r.status_code}, length: {len(r.text)}')

# Login with existing user
r = requests.post(f'{base}/api/login', json={'username':'testuser','password':'Test1234'})
print(f'Login: {r.status_code}')
token = r.json().get('access_token','')
headers = {'Authorization': f'Bearer {token}'}
print(f'Token received: {bool(token)}')

# Test trending
r = requests.get(f'{base}/api/movies/trending?page=1&per_page=5', headers=headers)
print(f'Trending: {r.status_code}, count: {len(r.json().get("movies",[]))}')
if r.ok:
    for m in r.json()['movies'][:3]:
        print(f'  - {m["title"]} (rating: {m["vote_average"]})')

# Test search
r = requests.get(f'{base}/api/movies/search?q=avatar', headers=headers)
print(f'Search avatar: {r.status_code}, count: {len(r.json().get("movies",[]))}')

# Test recommend
r = requests.get(f'{base}/api/movies/recommend/Avatar', headers=headers)
print(f'Recommend Avatar: {r.status_code}, count: {len(r.json().get("recommendations",[]))}')
if r.ok:
    for m in r.json()['recommendations'][:5]:
        print(f'  Similar: {m["title"]} (rating: {m["vote_average"]})')

print('\nAll tests complete!')
