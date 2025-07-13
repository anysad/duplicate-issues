from github import Github
import os
import re
import ollama

class DuplicateDeterminer:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repname = os.getenv('GITHUB_REPOSITORY')
        self.issue_number = os.getenv('ISSUE_NUMBER')
        self.github_client = Github(self.github_token)
        self.repo = self.github_client.get_repo(self.repname)
        self.full_transcript = [
            {'role': 'system', 'content': 'You are a helpful assistant if two different github issues are duplicates as if they are the same or very similar. You will be given two issues and you will return a boolean value. If they are duplicates, return True, otherwise return False. Do not return any other text.'}
        ]
        self.issue = self.repo.get_issue(int(self.issue_number))
        self.new_issue_text = self.get_issue_full_text(self.issue)
    
    def get_issue_description(self, text):
        match = re.search(r'Description.*?\n(.*?)(?:\n## |\Z)', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ' '
    
    def get_issue_str(self, text):
        match = re.search(r'Steps to Reproduce.*?\n(.*?)(?:\n## |\Z)', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def get_issue_full_text(self, issue):
        text = f'Title: {issue.title}\nDescription: {self.get_issue_description(issue.body)}\n'
        steps_to_reproduce = self.get_issue_str(issue.body)
        if steps_to_reproduce:
            text += f'Steps to Reproduce: {steps_to_reproduce}\n'
        return text
    
    def check_duplicate(self):
        similarities = []
        for issue in self.repo.get_issues(state='open'):
            if issue.number == int(self.issue_number):
                continue

            issue_text = self.get_issue_full_text(issue)
            self.full_transcript.append({'role': 'user', 'content': 'Is this issue a duplicate of the following issue?\nNew Issue:\n'+ self.new_issue_text + '\n\nExisting Issue:\n' + issue_text })

            ollama_response = ollama.chat(
                model='llama3',
                messages=self.full_transcript
            )

            response_content = ollama_response['message']['content']

            print(f'Comparing two issues: {self.issue_number} and {issue.number}')
            print(f'Response: {response_content}')

            if response_content.lower() == 'true':
                similarities.append(issue.number)

        if similarities:
            comment = '✍️ Potential duplicates:\n'
            for possible_issue in similarities:
                comment += f'- [#{possible_issue}]'
            self.issue.create_comment(comment)
        else:
            print('❌ No similiar issues were found.')


if  __name__ == '__main__':
    determiner = DuplicateDeterminer()
    determiner.check_duplicate()