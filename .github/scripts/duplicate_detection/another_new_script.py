import os
from fuzzywuzzy import fuzz
from github import Github
import re

token = os.getenv('GITHUB_TOKEN')
repname = os.getenv('GITHUB_REPOSITORY')
issue_number = os.getenv('ISSUE_NUMBER')

github_client = Github(token)
repo = github_client.get_repo(repname)
new_issue = repo.get_issue(int(issue_number))

DESCRIPTION_RE = re.compile(r'##\s*Description.*?\n(.*?)(?=\n## |\Z)', re.DOTALL)
STR_RE = re.compile(r'(?i)Steps to Reproduce:?\s*\n(.*?)(?:\n## |\Z)', re.DOTALL)

def get_issue_description(text):
    match = DESCRIPTION_RE.search(text)
    return match.group(1).strip() if match else ' '
    
def get_issue_str(text):
    match = STR_RE.search(text)
    return match.group(1).strip() if match else ' '
    
def get_issue_full_text(issue):
    text = f'Title: {issue.title}\nDescription: {get_issue_description(issue.body)}\n'
    steps_to_reproduce = get_issue_str(issue.body)
    if steps_to_reproduce:
        text += f'Steps to Reproduce: {steps_to_reproduce}\n'
    return text

def calculate_similarity(text1, text2):
    token_set_score = fuzz.token_set_ratio(text1, text2)
    partial_score = fuzz.partial_ratio(text1, text2)
    return round(0.8 * token_set_score + 0.2 * partial_score)

open_issues = repo.get_issues(state='open')
threshold = 65 # change this value to adjust sensitivity!!!
duplicates = []
for issue in open_issues:
    if issue.number == new_issue.number:
        continue
    similarity = calculate_similarity(get_issue_full_text(new_issue), get_issue_full_text(issue))
    print(similarity)
    if similarity > threshold:
        duplicates.append((issue.number, similarity))

if duplicates:
    comment_body = '✍️ Potential duplicates:\n'
    for dup in duplicates:
        comment_body += f'- #{dup[0]} (Similarity {dup[1]}%)\n'
    new_issue.create_comment(comment_body)
else:
    print('❌ No similiar issues were found.')