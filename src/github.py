import datetime
from pathlib import Path

from github import Github


# Class to push github commit
class GithubClient:
    def __init__(self, token="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"):
        self.token = token
        self.g = Github(self.token)
        self.repo = self.g.get_repo("COMP585Fall2022/Team-5")

    def update_file(self, file_path, commit_msg):
        content = Path(file_path).read_text()
        repo_file = self.repo.get_contents(str(file_path))
        self.repo.update_file(repo_file.path, commit_msg, content, repo_file.sha)
