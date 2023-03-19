from __future__ import annotations
from typing import ClassVar, Optional, TYPE_CHECKING

import attrs
import enum

from aiohttp import ClientSession
from utils import convert_to_date

if TYPE_CHECKING:
    from datetime import datetime


class GitHubInfoType(enum.Enum):
    issue = 0
    pull_request = 1


@attrs.define()
class GitHubUser:
    name: str
    avatar_url: str
    profile_url: str


@attrs.define(kw_only=True, repr=True)
class GitHubInfo:
    info_type: GitHubInfoType
    url: str
    comments_url: str

    number: str
    state: str
    state_reason: str
    title: str
    description: str
    number_of_comments: str
    closed_at: Optional[datetime] = attrs.field(converter=convert_to_date)
    created_at: Optional[datetime] = attrs.field(converter=convert_to_date)
    updated_at: Optional[datetime] = attrs.field(converter=convert_to_date)

    author: GitHubUser


class GitHubAPIClient:
    BASE_URL: ClassVar = "https://api.github.com"
    FETCH_REPO_URL: ClassVar = "/repos/{owner}/{repo_name}"
    FETCH_ISSUE_URL: ClassVar = "/repos/{owner}/{repo_name}/issues/{n_issue}"
    FETCH_PR_URL: ClassVar = "/repos/{owner}/{repo_name}/pulls/{n_pr}"
    
    # TODO
    # - implement a cache system using redis cache (redis-py)
    
    async def setup(self, token: str) -> None:
        self._token = token
        self._session = ClientSession(
            self.BASE_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        return

    async def close(self) -> None:
        await self._session.close()
    
    async def fetch_repository(self):
        pass

    async def fetch_issue_or_pr(self, owner: str, repo_name: str, n_issue_or_pr: str):
        response = await self._session.get(self.FETCH_ISSUE_URL.format(owner=owner, repo_name=repo_name, n_issue=n_issue_or_pr))
        data = await response.json()
        author = data["user"]

        if not "pull_request" in data.keys():
            return GitHubInfo(
                info_type=GitHubInfoType.issue,
                url=data.get("url"),
                comments_url=data.get("comments_url"),
                number=data.get("number"),
                state=data.get("state"),
                state_reason=data.get("state_reason"),
                title=data.get("title"),
                description=data.get("body"),
                number_of_comments=data.get("comments"),
                closed_at=data.get("closed_at"),
                updated_at=data.get("updated_at"),
                created_at=data.get("created_at"),
                author=GitHubUser(
                    name=author.get("login"),
                    avatar_url=author.get("avatar_url"),
                    profile_url=author.get("html_url"),
                ),
            )
        pr = data.get("pull_request")
        return GitHubInfo(
            info_type=GitHubInfoType.pull_request,
            url=pr.get("url"),
            comments_url=data.get("comments_url"),
                number=data.get("number"),
                state=data.get("state"),
                state_reason=data.get("state_reason"),
                title=data.get("title"),
                description=data.get("body"),
                number_of_comments=data.get("comments"),
                closed_at=data.get("closed_at"),
                updated_at=data.get("updated_at"),
                created_at=data.get("created_at"),
                author=GitHubUser(
                    name=author.get("login"),
                    avatar_url=author.get("avatar_url"),
                    profile_url=author.get("html_url"),
                ),
        )




import asyncio

g = GitHubAPIClient()
async def main():
    await g.setup("my_token")
    r = await g.fetch_issue_or_pr("DisnakeDev", "disnake", "1")
    print(r)
    await g.close()

asyncio.run(main())