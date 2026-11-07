from datetime import UTC, datetime

from fakes import FakeHttpClient, ok

from agent.adapters.feeds import FeedSource, HackerNewsSource
from agent.radar.lead import Source, collect_leads

SINCE = datetime(2026, 11, 6, 8, 0, tzinfo=UTC)

BLOG_FEED = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Blog</title>
  <item>
    <title>Sandboxing coding agents</title>
    <link>https://blog.example.com/sandboxes/?utm_source=rss</link>
    <pubDate>Fri, 06 Nov 2026 20:00:00 GMT</pubDate>
    <description>&lt;p&gt;How we run agents in &lt;b&gt;sandboxes&lt;/b&gt;.&lt;/p&gt;</description>
  </item>
  <item>
    <title>Old news</title>
    <link>https://blog.example.com/old</link>
    <pubDate>Mon, 02 Nov 2026 10:00:00 GMT</pubDate>
  </item>
  <item>
    <title>Evals in CI</title>
    <link>https://blog.example.com/evals</link>
    <pubDate>Sat, 07 Nov 2026 06:00:00 GMT</pubDate>
  </item>
</channel></rss>"""

RELEASES_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Releases</title>
  <entry>
    <title>v2.0.0</title>
    <link rel="alternate" href="https://github.com/acme/agent/releases/tag/v2.0.0"/>
    <updated>2026-11-06T12:00:00Z</updated>
    <content type="html">Breaking: new tool API</content>
  </entry>
</feed>"""

HN_SEARCH = """{"hits": [
  {"objectID": "41", "title": "Sandboxing coding agents", "points": 210,
   "url": "https://blog.example.com/sandboxes", "created_at_i": 1793995200},
  {"objectID": "42", "title": "Ask HN: How do you review AI-written code?", "points": 95,
   "url": null, "created_at_i": 1793984400}
]}"""


def blog_source(http: FakeHttpClient) -> FeedSource:
    return FeedSource(name="Blog", url="https://blog.example.com/feed", http=http)


def test_returns_feed_entries_published_since_the_cutoff_newest_first() -> None:
    http = FakeHttpClient({"https://blog.example.com/feed": ok(BLOG_FEED)})

    report = collect_leads([blog_source(http)], since=SINCE, posted_urls=set())

    assert [lead.title for lead in report.leads] == ["Evals in CI", "Sandboxing coding agents"]
    assert report.leads[1].summary == "How we run agents in sandboxes."
    assert report.leads[1].source == "Blog"


def test_reads_atom_feeds_such_as_github_releases() -> None:
    http = FakeHttpClient({"https://github.com/acme/agent/releases.atom": ok(RELEASES_FEED)})
    source = FeedSource(
        name="acme/agent releases", url="https://github.com/acme/agent/releases.atom", http=http
    )

    report = collect_leads([source], since=SINCE, posted_urls=set())

    assert [(lead.title, lead.url) for lead in report.leads] == [
        ("v2.0.0", "https://github.com/acme/agent/releases/tag/v2.0.0")
    ]


def test_hacker_news_stories_without_a_link_point_to_the_discussion() -> None:
    http = FakeHttpClient({"https://hn.algolia.com/api/v1/search": ok(HN_SEARCH)})
    source = HackerNewsSource(name="HN: code review", query="AI code review", http=http)

    report = collect_leads([source], since=SINCE, posted_urls=set())

    assert [(lead.url, lead.points) for lead in report.leads] == [
        ("https://blog.example.com/sandboxes", 210),
        ("https://news.ycombinator.com/item?id=42", 95),
    ]
    assert http.requests[0].params["query"] == "AI code review"


def test_the_same_link_from_two_sources_becomes_one_lead() -> None:
    http = FakeHttpClient(
        {
            "https://blog.example.com/feed": ok(BLOG_FEED),
            "https://hn.algolia.com/api/v1/search": ok(HN_SEARCH),
        }
    )
    sources: list[Source] = [
        blog_source(http),
        HackerNewsSource(name="HN", query="agents", http=http),
    ]

    report = collect_leads(sources, since=SINCE, posted_urls=set())

    sandbox_leads = [lead for lead in report.leads if "sandboxes" in lead.url]
    assert len(sandbox_leads) == 1
    assert sandbox_leads[0].source == "Blog"


def test_leaves_out_links_already_posted_in_a_radar() -> None:
    http = FakeHttpClient({"https://blog.example.com/feed": ok(BLOG_FEED)})

    report = collect_leads(
        [blog_source(http)], since=SINCE, posted_urls={"https://blog.example.com/sandboxes"}
    )

    assert [lead.title for lead in report.leads] == ["Evals in CI"]


def test_a_broken_source_is_reported_and_the_others_still_return_leads() -> None:
    http = FakeHttpClient({"https://blog.example.com/feed": ok(BLOG_FEED)})
    broken = FeedSource(name="Dead blog", url="https://dead.example.com/feed", http=http)

    report = collect_leads([broken, blog_source(http)], since=SINCE, posted_urls=set())

    assert len(report.leads) == 2
    assert [failure.source for failure in report.failures] == ["Dead blog"]
    assert "dead.example.com" in report.failures[0].error
