from __future__ import annotations
from typing import ClassVar, Optional, List, Tuple

import attrs
import enum
import re

from datetime import datetime
from logging import getLogger


from aiohttp import ClientSession
from disnake import Event
from disnake.ext import commands

from config import BotConfig
from bot import PrismoBot

__all__: Tuple[str, ...] = (
    "GitHubInfoType",
    "GitHubUserType",
    "GitHubAPIClient",
)

MAXIMUM_ISSUES = 5
# thanks to monty python
# https://github.com/onerandomusername/monty-python/blob/1c644bc006a9e885d32c2f1096416787c9e36207/monty/exts/info/github_info.py#L68
AUTOMATIC_REGEX = re.compile(
    r"((?P<org>[a-zA-Z0-9][a-zA-Z0-9\-]{1,39})\/)?(?P<repo>[\w\-\.]{1,100})#(?P<number>[0-9]+)"
)

_log = getLogger(__name__)

def convert_to_date(date: Optional[str]) -> Optional[datetime]:
    if not date:
        return None
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")


class GitHubInfoType(enum.Enum):
    issue = 0
    pull_request = 1


class GitHubUserType(enum.Enum):
    user = 0
    organization = 1


@attrs.define()
class GitHubUser:
    user_type: GitHubUserType
    name: str
    avatar_url: str
    profile_url: str


@attrs.define(repr=True)
class GitHubRepoStats:
    forks_count: str
    stars: str
    default_branch: str
    open_issues_and_prs: str
    topics: List[str]
    archived: bool

    pushed_at: Optional[datetime] = attrs.field(converter=convert_to_date)
    created_at: datetime = attrs.field(converter=convert_to_date)
    updated_at: Optional[datetime] = attrs.field(converter=convert_to_date)


@attrs.define(repr=True)
class GitHubRepo:
    full_name: str
    description: str
    fork: bool
    owner: GitHubUser
    url: str

    stats: GitHubRepoStats


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
    created_at: datetime = attrs.field(converter=convert_to_date)
    updated_at: Optional[datetime] = attrs.field(converter=convert_to_date)

    author: GitHubUser


class GitHubAPIClient:
    BASE_URL: ClassVar = "https://api.github.com"
    FETCH_REPO_URL: ClassVar = "/repos/{owner}/{repo_name}"
    FETCH_ISSUE_URL: ClassVar = "/repos/{owner}/{repo_name}/issues/{n_issue}"
    FETCH_PR_URL: ClassVar = "/repos/{owner}/{repo_name}/pulls/{n_pr}"
    
    # TODO
    # - implement a cache system using redis cache (redis-py)

    def __init__(self) -> None:
        self._setted_up: bool = False
    
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
    
    @property
    def is_ready(self) -> bool:
        if not self._setted_up:
            return False
        return True

    async def close(self) -> None:
        await self._session.close()
    
    async def fetch_repository(self, owner: str, repo_name: str) -> GitHubRepo:
        response = await self._session.get(self.FETCH_REPO_URL.format(owner=owner, repo_name=repo_name))
        data = await response.json()
        author = data["owner"]

        return GitHubRepo(
            full_name=data.get("full_name"),
            description=data.get("description"),
            fork=data.get("fork"),
            owner=GitHubUser(
                user_type=(
                    GitHubUserType.user if author.get("type") == "User"
                    else GitHubUserType.organization 
                ),
                name=author.get("login"),
                avatar_url=author.get("avatar_url"),
                profile_url=author.get("html_url"),
            ),
            url=data.get("html_url"),
            stats=GitHubRepoStats(
                forks_count=data.get("forks_count"),
                stars=data.get("stargazers_count"),
                default_branch=data.get("default_branch"),
                open_issues_and_prs=data.get("open_issues"),
                topics=data.get("topics"),
                archived=data.get("archived"),
                pushed_at=data.get("pushed_at"),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
            )
        )

    async def fetch_issue_or_pr(self, owner: str, repo_name: str, n_issue_or_pr: str) -> GitHubInfo:
        response = await self._session.get(self.FETCH_ISSUE_URL.format(owner=owner, repo_name=repo_name, n_issue=n_issue_or_pr))
        data = await response.json()
        author = data["user"]

        return GitHubInfo(
            info_type=(
                GitHubInfoType.pull_request if "pull_request" in data.keys()
                else GitHubInfoType.issue
            ),
            url=(
                (data.get("pull_request")).get("url") if "pull_request" in data.keys()
                else data.get("url")
            ),
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
                user_type=(
                    GitHubUserType.user if author.get("type") == "User"
                    else GitHubUserType.organization 
                ),
                name=author.get("login"),
                avatar_url=author.get("avatar_url"),
                profile_url=author.get("html_url"),
            ),
        )


class GitHub(commands.Cog):
    def __init__(self, bot: PrismoBot) -> None:
        self.bot = bot
        self.github_client = GitHubAPIClient()

    @commands.Cog.listener(Event.connect)
    async def open_gh_client(self):
        _log.info("Opening the Github client")
        await self.github_client.setup(BotConfig.github_token)

    @commands.Cog.listener(Event.disconnect)
    async def close_gh_client(self):
        _log.info("Closing the Github client")
        await self.github_client.close()
    
    @commands.command()
    async def repo(self, ctx: commands.Context[PrismoBot], owner: str, name: str):
        await ctx.send(repr(await self.github_client.fetch_repository(owner, name)))

    @commands.Cog.listener(Event.message)
    async def handle_issues_or_prs_mentions(self, ctx: commands.Context[PrismoBot]):
        pass


def setup(bot: PrismoBot):
    bot.add_cog(GitHub(bot))