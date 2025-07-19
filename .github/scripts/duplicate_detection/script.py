from sentence_transformers import SentenceTransformer, util
from github import Github
from fuzzywuzzy import fuzz
import os
import re
import random

model = SentenceTransformer('all-MiniLM-L6-v2')

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

def calculate_similarity(text1, text2, weight_embed=0.7, weight_fuzz=0.3):
    embeddings = model.encode([text1, text2])
    cosine_score = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
    fuzz_score = round(fuzz.token_set_ratio(text1, text2) / 100.0)
    combined = weight_embed * cosine_score + weight_fuzz * fuzz_score
    return round(combined * 100)

similarities = []
threshold = 80 # change this value to adjust sensitivity!!!
for issue in repo.get_issues(state='open'):
    if issue.number == new_issue.number:
        continue

    similarity = calculate_similarity(get_issue_full_text(new_issue), get_issue_full_text(issue))
    print(similarity)

    if similarity > threshold:
        similarities.append((issue.number, similarity, issue.title))

if similarities:
    if random.random() < 0.01: # joke comment 1% of the time
        comment = 'dude... I think you lowkey messed up dawg... this is like the 10th time I\'ve seen this issue, you should really check the issues before creating a new one... anyways here are the potential duplicates:\n'
    else:
        comment = '✍️ Potential duplicates:\n'
    for number, similarity, title in similarities:
        print(f'Similarity: {similarity}%')
        comment += f'- #{number} ({similarity}%)\n'
    new_issue.create_comment(comment)
else:
    print('❌ No similiar issues were found.')