from github import Github
import os
import re
import ollama

DESCRIPTION_RE = re.compile(r'Description.*?\n(.*?)(?:\n## |\Z)', re.DOTALL)
STR_RE = re.compile(r'Steps to Reproduce.*?\n(.*?)(?:\n## |\Z)', re.DOTALL)
ollama.embeddings()

class DuplicateDeterminer:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repname = os.getenv('GITHUB_REPOSITORY')
        self.new_issue_number = os.getenv('ISSUE_NUMBER')

        self.github_client = Github(self.github_token)
        self.repo = self.github_client.get_repo(self.repname)
        self.new_issue = self.repo.get_issue(int(self.issue_number))

        self.system_prompt = {
            'role': 'system',
            'content': 'You are an expert Ai designed to detect whether two GitHub issues describe the same or nearly the same underlying problem. You will be give two issues: a new issue and an existing issue each containing a title, description, and steps to reproduce. Your task is to output a single integer between 0 and 100, which represents how similar the two issues are, with 0 being completely different and 100 being identical. Use this scale as a guide: 90-100 means that it is nearly identical, duplicate bugs or requests with minor wording changes. 70-89 mean a strong overlap, where same core issue is described but there are differences in reproduction or symptoms. 50-69 means a related topic or component, but not the same issue. Below 50 mean clearly different issues. Only return the number. Do not include a percent sign, explanation, or any other text in your response.'
        }
    
    # def get_issue_description(self, text):
    #     match = DESCRIPTION_RE.search(text)
    #     return match.group(1).strip() if match else ' '
    
    # def get_issue_str(self, text):
    #     match = STR_RE.search(text)
    #     return match.group(1).strip() if match else ' '
    
    # def get_issue_full_text(self, issue):
    #     text = f'Title: {issue.title}\nDescription: {self.get_issue_description(issue.body)}\n'
    #     steps_to_reproduce = self.get_issue_str(issue.body)
    #     if steps_to_reproduce:
    #         text += f'Steps to Reproduce: {steps_to_reproduce}\n'
    #     return text
    
    def check_duplicates(self):
        duplicates = []
        for issue in self.repo.get_issues(state='open'):
            if issue.number == int(self.new_issue_number):
                continue

            messages = [
                self.system_prompt,
                {
                    'role': 'user',
                    'content': f'Are these two issues the same or nearly the same? New Issue:\n <TITLE>${self.new_issue.title}</TITLE>\n <DESCRIPTION>${self.new_issue.body}</DESCRIPTION>\n\n Existing Issue:\n <TITLE>${issue.title}</TITLE>\n <DESCRIPTION>${issue.body}</DESCRIPTION>\n'
                }
            ]

            response = ollama.chat(model='qwen3:0.6b', messages=messages)
            result = response['message']['content']

            print(result)

            # if result.lower() == 'true':
            #     duplicates.append(issue.number)

        if duplicates:
            comment = '✍️ Potential duplicates:\n'
            for possible_issue in duplicates:
                comment += f'- [#{possible_issue}]\n'
            self.issue.create_comment(comment)
        else:
            print('❌ No similiar issues were found.')


if  __name__ == '__main__':
    DuplicateDeterminer().check_duplicates()