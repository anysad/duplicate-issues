from github import Github
import os
import re
import ollama

DESCRIPTION_RE = re.compile(r'Description.*?\n(.*?)(?:\n## |\Z)', re.DOTALL)
STR_RE = re.compile(r'Steps to Reproduce.*?\n(.*?)(?:\n## |\Z)', re.DOTALL)

class DuplicateDeterminer:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repname = os.getenv('GITHUB_REPOSITORY')
        self.issue_number = os.getenv('ISSUE_NUMBER')

        self.github_client = Github(self.github_token)
        self.repo = self.github_client.get_repo(self.repname)
        self.issue = self.repo.get_issue(int(self.issue_number))
        self.new_issue_text = self.get_issue_full_text(self.issue)

        self.system_prompt = {
            'role': 'system',
            'content': 'You are an expert assistant designed to determine if two GitHub issues describe the same underlying problem. You will be given a "New Issue" and an "Existing Issue". If they clearly describe the same or very similar issue, return **only** the word "True". If they are unrelated or different issues, return **only** the word "False". Do not explain your reasoning. Do not include any other text.'
        }
    
    def get_issue_description(self, text):
        match = DESCRIPTION_RE.search(text)
        return match.group(1).strip() if match else ' '
    
    def get_issue_str(self, text):
        match = STR_RE.search(text)
        return match.group(1).strip() if match else ' '
    
    def get_issue_full_text(self, issue):
        text = f'Title: {issue.title}\nDescription: {self.get_issue_description(issue.body)}\n'
        steps_to_reproduce = self.get_issue_str(issue.body)
        if steps_to_reproduce:
            text += f'Steps to Reproduce: {steps_to_reproduce}\n'
        return text
    
    def check_duplicates(self):
        duplicates = []
        for issue in self.repo.get_issues(state='open'):
            if issue.number == int(self.issue_number):
                continue

            issue_text = self.get_issue_full_text(issue)
            messages = [
                self.system_prompt,
                {
                    'role': 'user',
                    'content': 'Is this issue a duplicate of the following issue?\nNew Issue:\n'+ self.new_issue_text + '\n\nExisting Issue:\n' + issue_text
                }
            ]

            response = ollama.chat(model='llama3.2:3b', messages=messages)
            result = response['message']['content']

            if result.lower() == 'true':
                duplicates.append(issue.number)

        if duplicates:
            comment = '✍️ Potential duplicates:\n'
            for possible_issue in duplicates:
                comment += f'- [#{possible_issue}]\n'
            self.issue.create_comment(comment)
        else:
            print('❌ No similiar issues were found.')


if  __name__ == '__main__':
    DuplicateDeterminer().check_duplicates()