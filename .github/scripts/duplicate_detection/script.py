from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from github import Github
import os
import re

model = SentenceTransformer('all-MiniLM-L6-v2')

token = os.getenv('GITHUB_TOKEN')
repname = os.getenv('GITHUB_REPOSITORY')
issue_number = os.getenv('ISSUE_NUMBER')

github_client = Github(token)
repo = github_client.get_repo(repname)

def get_description(text):
    match = re.search(r'Description.*?\n(.*?)(?:\n## |\Z)', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def get_str(text):
    match = re.search(r'Steps to Reproduce.*?\n(.*?)(?:\n## |\Z)', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

new_issue = repo.get_issue(int(issue_number))

new_issue_desc = get_description(new_issue.body)
new_issue_str = get_str(new_issue.body)
new_issue_text = new_issue.title + " " + (new_issue_desc or " ") + " " + (new_issue_str or " ")
new_issue_embedding = model.encode([new_issue_text])

similarities = []
for issue in repo.get_issues(state='open'):
    if issue.number == new_issue.number:
        continue

    issue_desc = get_description(issue.body)
    issue_str = get_str(issue.body)
    issue_text = issue.title + " " + (issue_desc or " ") + " " + (issue_str or " ")
    issue_embedding = model.encode([issue_text])

    similarity = cosine_similarity(new_issue_embedding, issue_embedding)[0][0]
    print(similarity)

    if similarity > 0.69: # nice
        similarities.append((issue.number, similarity, issue.title))

if similarities:
    comment = "✍️ Potential duplicates:\n"
    for number, similarity, title in similarities:
        comment += f"- #{number} ({similarity * 100:.1f}%)\n"
    new_issue.create_comment(comment)
else:
    print('❌ No similiar issues were found.')