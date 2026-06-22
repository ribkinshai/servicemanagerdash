"""שכבת אחסון מבוססת GitHub - שומרת את כל המשימות כקובץ JSON ברפו."""

import json
import base64
from github import Github, GithubException, Auth


class GitHubStorage:
    """
    שמירת המשימות כקובץ JSON ברפו של GitHub.
    כל שמירה יוצרת commit, כך שיש לך היסטוריה מלאה של שינויים.
    """

    def __init__(
        self,
        token: str,
        repo_name: str,
        file_path: str = "data/tasks.json",
        branch: str = "main",
    ):
        auth = Auth.Token(token)
        self.gh = Github(auth=auth)
        self.repo_name = repo_name
        self.repo = self.gh.get_repo(repo_name)
        self.file_path = file_path
        self.branch = branch
        self._sha = None  # SHA של הגרסה האחרונה שנטענה (נדרש לעדכון)

    def load(self) -> list:
        """טעינת משימות מ-GitHub. מחזיר [] אם הקובץ עוד לא קיים."""
        try:
            file = self.repo.get_contents(self.file_path, ref=self.branch)
            self._sha = file.sha
            content = base64.b64decode(file.content).decode("utf-8")
            data = json.loads(content) if content.strip() else []
            return data if isinstance(data, list) else []
        except GithubException as e:
            if e.status == 404:
                self._sha = None
                return []
            raise

    def save(self, tasks: list, commit_message: str = "Update tasks") -> None:
        """שמירת המשימות ל-GitHub כ-commit חדש."""
        content = json.dumps(tasks, indent=2, ensure_ascii=False)
        if self._sha:
            result = self.repo.update_file(
                path=self.file_path,
                message=commit_message,
                content=content,
                sha=self._sha,
                branch=self.branch,
            )
        else:
            result = self.repo.create_file(
                path=self.file_path,
                message=commit_message,
                content=content,
                branch=self.branch,
            )
        # עדכון ה-SHA לשמירה הבאה
        self._sha = result["content"].sha
