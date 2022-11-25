import base64
from pathlib import Path

import github

from src.config import GITHUB_TOKEN


class GithubClient:
    def __init__(self):
        try:
            with open(GITHUB_TOKEN, "r") as f:
                github_token = f.readline()
                self.token = github_token
        except Exception:
            print("Read github token failed")
        self.g = github.Github(self.token)
        self.repo = self.g.get_repo("COMP585Fall2022/Team-5")

    def update_file(self, ab_path, file_path, commit_msg):
        content = Path(ab_path).read_text()
        repo_file = self.repo.get_contents(str(file_path))
        self.repo.update_file(repo_file.path, commit_msg, content, repo_file.sha)

    def update_files(self, file_paths, commit_msg):
        elements = []

        for ab_path, file_path, file_format in file_paths:
            print(file_path, file_format)
            if file_format == "base64":
                content = base64.b64encode(open(Path(ab_path), "rb").read())
                content = content.decode("utf-8")
            else:
                content = Path(ab_path).read_text()
            blob = self.repo.create_git_blob(content, file_format)
            element = github.InputGitTreeElement(
                path=file_path, mode="100644", type="blob", sha=blob.sha
            )
            elements.append(element)

        head_sha = self.repo.get_branch("main").commit.sha
        base_tree = self.repo.get_git_tree(sha=head_sha)
        tree = self.repo.create_git_tree(elements, base_tree)
        parent = self.repo.get_git_commit(sha=head_sha)
        commit = self.repo.create_git_commit(commit_msg, tree, [parent])
        main_ref = self.repo.get_git_ref("heads/main")
        main_ref.edit(sha=commit.sha)
