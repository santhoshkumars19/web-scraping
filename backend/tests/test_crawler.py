"""
tests/test_crawler.py

Comprehensive unit and integration tests for the Website Crawler (Backend Step 5):
  • Link extraction & relative URL resolution
  • Domain boundary & social media filtering
  • Subdomain handling
  • Page classification & heuristic scoring
  • URL frontier priority queue & depth/page limits
  • Robots.txt parsing & compliance
  • HTTP crawler content-type, size, and redirect boundaries
  • Playwright fallback shell detection
  • Single website crawl lifecycle
  • CrawlerService DB persistence & SourcePage upsert
  • Website failure isolation (one failed site does not fail others or the task)
  • Idempotency of re-crawling
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization, task_organizations
from app.models.scraping_log import ScrapingLog
from app.models.scraping_task import ScrapingTask
from app.models.source_page import SourcePage
from app.models.user import User
from app.models.website import Website
from app.services.crawler import (
    HttpCrawler,
    LinkExtractor,
    PageClassifier,
    PlaywrightCrawler,
    RobotsChecker,
    UrlFrontier,
    WebsiteCrawler,
)
from app.services.crawler.exceptions import (
    AccessDeniedError,
    CrawlerError,
    DomainNotAllowedError,
    NonHtmlContentError,
    RedirectLimitError,
    ResponseTooLargeError,
)
from app.services.crawler_service import CrawlerService


# ── 1. Link Extractor & Normalization Tests ────────────────────────────────────

def test_link_extractor_relative_and_fragments() -> None:
    html = """
    <html>
        <head><title>  St. Paul's High School  </title></head>
        <body>
            <a href="/about-us">About</a>
            <a href="contact.html#form">Contact</a>
            <a href="admissions/apply">Admissions</a>
            <a href="#section">Internal anchor</a>
            <a href="mailto:info@school.org">Mail</a>
            <a href="tel:+911234567890">Phone</a>
            <a href="javascript:void(0)">JS</a>
            <a href="/prospectus.pdf">PDF File</a>
            <a href="/logo.png">Logo</a>
        </body>
    </html>
    """
    title, links = LinkExtractor.extract_links(
        html=html,
        base_url="https://stpauls.example/index.html",
        website_domain="stpauls.example",
        depth=0,
    )

    assert title == "St. Paul's High School"
    assert len(links) == 3

    urls = [link.url for link in links]
    assert "https://stpauls.example/about-us" in urls
    assert "https://stpauls.example/contact.html" in urls
    assert "https://stpauls.example/admissions/apply" in urls


def test_link_extractor_domain_boundaries() -> None:
    html = """
    <html>
        <body>
            <a href="https://stpauls.example/about">Allowed internal</a>
            <a href="https://facebook.com/stpauls">External Facebook</a>
            <a href="https://twitter.com/stpauls">External Twitter</a>
            <a href="https://competitor.example/page">External Site</a>
            <a href="https://portal.stpauls.example/login">Subdomain</a>
        </body>
    </html>
    """
    # 1. With subdomains disallowed
    _, links_no_sub = LinkExtractor.extract_links(
        html=html,
        base_url="https://stpauls.example",
        website_domain="stpauls.example",
        allow_subdomains=False,
    )
    urls_no_sub = [l.url for l in links_no_sub]
    assert "https://stpauls.example/about" in urls_no_sub
    assert "https://facebook.com/stpauls" not in urls_no_sub
    assert "https://competitor.example/page" not in urls_no_sub
    assert "https://portal.stpauls.example/login" not in urls_no_sub

    # 2. With subdomains allowed
    _, links_with_sub = LinkExtractor.extract_links(
        html=html,
        base_url="https://stpauls.example",
        website_domain="stpauls.example",
        allow_subdomains=True,
    )
    urls_with_sub = [l.url for l in links_with_sub]
    assert "https://portal.stpauls.example/login" in urls_with_sub


# ── 2. Page Classifier Tests ──────────────────────────────────────────────────

def test_page_classifier_heuristics() -> None:
    assert PageClassifier.classify("https://school.example/") == "HOME"
    assert PageClassifier.classify("https://school.example/index.html") == "HOME"
    assert PageClassifier.classify("https://school.example/contact-us") == "CONTACT"
    assert PageClassifier.classify("https://school.example/about-school") == "ABOUT"
    assert PageClassifier.classify("https://school.example/admission-process") == "ADMISSIONS"
    assert PageClassifier.classify("https://school.example/principals-desk") == "PRINCIPAL"
    assert PageClassifier.classify("https://school.example/our-faculty") == "FACULTY"
    assert PageClassifier.classify("https://school.example/management-committee") == "MANAGEMENT"
    assert PageClassifier.classify("https://school.example/campus-infrastructure") == "INFRASTRUCTURE"
    assert PageClassifier.classify("https://school.example/branch-offices") == "BRANCH"
    assert PageClassifier.classify("https://school.example/random-gallery") == "OTHER"


def test_page_classifier_priority_weighting() -> None:
    # Contact should have higher priority (lower integer) than About and Other
    p_contact = PageClassifier.calculate_priority("CONTACT", depth=1, prioritize_contact=True)
    p_about = PageClassifier.calculate_priority("ABOUT", depth=1, prioritize_about=True)
    p_other = PageClassifier.calculate_priority("OTHER", depth=1)

    assert p_contact < p_about < p_other


# ── 3. URL Frontier Tests ─────────────────────────────────────────────────────

def test_url_frontier_queue_and_limits() -> None:
    frontier = UrlFrontier(max_pages=3, max_depth=2, prioritize_contact=True, prioritize_about=True)

    # Adding initial links
    assert frontier.add("https://school.example/", depth=0, tentative_type="HOME") is True
    assert frontier.add("https://school.example/about", depth=1, tentative_type="ABOUT") is True
    assert frontier.add("https://school.example/contact", depth=1, tentative_type="CONTACT") is True
    assert frontier.add("https://school.example/gallery", depth=1, tentative_type="OTHER") is True

    # Depth beyond max_depth is rejected
    assert frontier.add("https://school.example/too-deep", depth=3, tentative_type="OTHER") is False

    # Duplicates rejected
    assert frontier.add("https://school.example/about/", depth=1) is False

    # Check order: HOME (depth 0) first
    item1 = frontier.pop()
    assert item1 is not None and item1.normalized_url == "https://school.example/"
    frontier.mark_visited(item1.normalized_url)


    # CONTACT (p=11) should come before ABOUT (p=21) and OTHER (p=51)
    item2 = frontier.pop()
    assert item2 is not None and item2.normalized_url == "https://school.example/contact"
    frontier.mark_visited(item2.normalized_url)

    item3 = frontier.pop()
    assert item3 is not None and item3.normalized_url == "https://school.example/about"
    frontier.mark_visited(item3.normalized_url)

    # max_pages reached (3), has_more is now False
    assert frontier.has_more() is False
    assert frontier.pop() is None


# ── 4. Robots.txt Checker Tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_robots_checker() -> None:
    robots_content = """
    User-agent: *
    Disallow: /admin/
    Disallow: /secret-page
    Allow: /
    """

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=robots_content)
        return httpx.Response(200, text="OK")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        checker = RobotsChecker()
        assert await checker.is_allowed("https://mock.example/about", client=client) is True
        assert await checker.is_allowed("https://mock.example/admin/settings", client=client) is False
        assert await checker.is_allowed("https://mock.example/secret-page", client=client) is False


@pytest.mark.asyncio
async def test_robots_checker_missing_file() -> None:
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        checker = RobotsChecker()
        # 404 robots.txt allows crawling everything
        assert await checker.is_allowed("https://mock404.example/any-page", client=client) is True


# ── 5. HTTP Crawler Guards Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_http_crawler_non_html_rejection() -> None:
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "application/pdf"},
            content=b"%PDF-1.4 simulated pdf",
        )

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        crawler = HttpCrawler()
        with pytest.raises(NonHtmlContentError) as exc_info:
            await crawler.fetch("https://school.example/brochure.pdf", website_domain="school.example", client=client)
        assert exc_info.value.code == "NON_HTML_CONTENT"


@pytest.mark.asyncio
async def test_http_crawler_oversized_response() -> None:
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html", "Content-Length": "100000000"},
            content=b"x" * 1000,
        )

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        crawler = HttpCrawler(max_response_size_bytes=500)
        with pytest.raises(ResponseTooLargeError):
            await crawler.fetch("https://school.example/huge", website_domain="school.example", client=client)


@pytest.mark.asyncio
async def test_http_crawler_off_domain_redirect() -> None:
    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/redirect-out":
            return httpx.Response(302, headers={"Location": "https://external.example/landing"})
        return httpx.Response(200, text="Hello")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        crawler = HttpCrawler()
        with pytest.raises(DomainNotAllowedError):
            await crawler.fetch("https://school.example/redirect-out", website_domain="school.example", client=client)


# ── 6. Playwright Fallback Detection Tests ────────────────────────────────────

def test_playwright_js_shell_detection() -> None:
    shell_html = """
    <!DOCTYPE html>
    <html>
        <head><title>React App</title></head>
        <body>
            <noscript>You need to enable JavaScript to run this app.</noscript>
            <div id="root"></div>
        </body>
    </html>
    """
    assert PlaywrightCrawler.is_js_shell(shell_html, internal_links_count=0) is True

    normal_html = """
    <!DOCTYPE html>
    <html>
        <head><title>St. Paul's School</title></head>
        <body>
            <h1>Welcome to St. Paul's School</h1>
            <p>We provide exceptional education for students in grades K-12 with comprehensive modern facilities.</p>
            <a href="/about">About Us</a>
            <a href="/contact">Contact</a>
            <a href="/admissions">Admissions</a>
        </body>
    </html>
    """
    assert PlaywrightCrawler.is_js_shell(normal_html, internal_links_count=3) is False


# ── 7. Single Website Crawler Integration Test ────────────────────────────────

@pytest.mark.asyncio
async def test_website_crawler_lifecycle() -> None:
    site_html = {
        "/": """
            <html>
                <head><title>ABC Academy</title></head>
                <body>
                    <h1>ABC Academy</h1>
                    <a href="/about">About</a>
                    <a href="/contact">Contact</a>
                    <a href="https://external.example/out">External</a>
                </body>
            </html>
        """,
        "/about": """
            <html>
                <head><title>About ABC Academy</title></head>
                <body><p>Our history and mission</p><a href="/history">History</a></body>
            </html>
        """,
        "/contact": """
            <html>
                <head><title>Contact ABC Academy</title></head>
                <body><p>Get in touch</p></body>
            </html>
        """,
        "/history": """
            <html><head><title>History</title></head><body><p>Deep page</p></body></html>
        """,
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/robots.txt":
            return httpx.Response(404, text="No robots")
        content = site_html.get(path)
        if content:
            return httpx.Response(200, headers={"Content-Type": "text/html"}, text=content)
        return httpx.Response(404, text="Not Found")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        http_crawler = HttpCrawler(client=client)
        crawler = WebsiteCrawler(http_crawler=http_crawler, crawl_delay=0.0)

        events: list[str] = []

        async def on_ev(ev_type: str, msg: str, url: str | None) -> None:
            events.append(ev_type)

        res = await crawler.crawl(
            website_id=uuid.uuid4(),
            root_url="https://abc.example/",
            max_pages=5,
            max_depth=1,  # Should NOT crawl /history (which is at depth 2)
            on_event=on_ev,
        )

        assert res.status == "CRAWLED"
        assert res.pages_crawled == 3  # /, /about, /contact
        assert "PAGE_CRAWLED" in events

        urls_crawled = [p.normalized_url for p in res.pages]
        assert "https://abc.example/" in urls_crawled
        assert "https://abc.example/about" in urls_crawled

        assert "https://abc.example/contact" in urls_crawled
        assert "https://abc.example/history" not in urls_crawled  # Excluded due to depth 1


# ── 8. CrawlerService Integration & DB Persistence Tests ───────────────────────

@pytest.mark.asyncio
async def test_crawler_service_task_workflow(db_session: AsyncSession) -> None:
    # 1. Create User
    user = User(
        name="Scout User",
        email="scout@example.com",
        password_hash="dummy_hash",
        role="USER",
    )
    db_session.add(user)
    await db_session.flush()

    # 2. Create Task
    task = ScrapingTask(
        task_id="TASK-000501",
        user_id=user.id,
        location="Puducherry",
        keyword="CBSE Schools",
        status="RUNNING",
        current_stage="FINDING_WEBSITES",
        progress=15,
        max_pages_per_site=5,
        crawl_depth=2,
    )
    db_session.add(task)
    await db_session.flush()

    # 3. Create Organizations and Websites
    org1 = Organization(name="St. Patrick School", city="Puducherry")
    db_session.add(org1)
    await db_session.flush()

    # Associate Org with Task
    await db_session.execute(
        task_organizations.insert().values(task_id=task.id, organization_id=org1.id)
    )

    web1 = Website(
        organization_id=org1.id,
        url="https://stpatrick.example",
        normalized_url="https://stpatrick.example",
        domain="stpatrick.example",
        status="PENDING",
    )
    db_session.add(web1)
    await db_session.commit()

    # Mock website response
    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404, text="")
        if request.url.path in ("/", ""):
            return httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text="""
                <html>
                    <head><title>St Patrick School Official</title></head>
                    <body>
                        <h1>St Patrick School</h1>
                        <a href="/contact-us">Contact Us</a>
                        <a href="/admissions">Admissions</a>
                    </body>
                </html>
                """,
            )
        elif request.url.path == "/contact-us":
            return httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text="<html><head><title>Contact St Patrick</title></head><body>Phone: 123</body></html>",
            )
        elif request.url.path == "/admissions":
            return httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text="<html><head><title>Admissions Form</title></head><body>Apply now</body></html>",
            )
        return httpx.Response(404, text="Not Found")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        http_crawler = HttpCrawler(client=client)
        crawler = WebsiteCrawler(http_crawler=http_crawler, crawl_delay=0.0)
        service = CrawlerService(session=db_session, crawler=crawler)

        summary = await service.crawl_for_task(task.task_id)

    # Verify Summary
    assert summary.total_websites == 1
    assert summary.websites_crawled == 1
    assert summary.failed_websites == 0
    assert summary.total_pages_stored == 3
    assert summary.next_stage == "EXTRACTING"

    # Verify Task Updates in DB
    refreshed_task = await db_session.get(ScrapingTask, task.id)
    assert refreshed_task.current_stage == "EXTRACTING"
    assert refreshed_task.websites_crawled == 1
    assert refreshed_task.progress == 50

    # Verify Website Status
    refreshed_web = await db_session.get(Website, web1.id)
    assert refreshed_web.status == "CRAWLED"
    assert refreshed_web.last_crawled_at is not None

    # Verify SourcePages persisted
    stmt_pages = select(SourcePage).where(SourcePage.website_id == web1.id)
    res_pages = await db_session.execute(stmt_pages)
    pages = list(res_pages.scalars().all())
    assert len(pages) == 3

    page_types = {p.page_type for p in pages}
    assert "HOME" in page_types
    assert "CONTACT" in page_types
    assert "ADMISSIONS" in page_types


# ── 9. Failure Isolation Test ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_crawler_service_failure_isolation(db_session: AsyncSession) -> None:
    """A failing website (e.g. 500 error / 404) must not fail other websites or the task."""
    user = User(
        name="Isolation User",
        email="isolation@example.com",
        password_hash="dummy_hash",
        role="USER",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id="TASK-000502",
        user_id=user.id,
        location="Puducherry",
        keyword="Schools",
        status="RUNNING",
        current_stage="FINDING_WEBSITES",
    )
    db_session.add(task)
    await db_session.flush()

    # Site 1: Broken / Crashing site
    org1 = Organization(name="Broken School", city="Puducherry")
    db_session.add(org1)
    await db_session.flush()
    await db_session.execute(
        task_organizations.insert().values(task_id=task.id, organization_id=org1.id)
    )
    site_broken = Website(
        organization_id=org1.id,
        url="https://broken.example",
        normalized_url="https://broken.example",
        domain="broken.example",
        status="PENDING",
    )
    db_session.add(site_broken)

    # Site 2: Healthy site
    org2 = Organization(name="Healthy School", city="Puducherry")
    db_session.add(org2)
    await db_session.flush()
    await db_session.execute(
        task_organizations.insert().values(task_id=task.id, organization_id=org2.id)
    )
    site_healthy = Website(
        organization_id=org2.id,
        url="https://healthy.example",
        normalized_url="https://healthy.example",
        domain="healthy.example",
        status="PENDING",
    )
    db_session.add(site_healthy)
    await db_session.commit()

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if "broken.example" in request.url.host:
            return httpx.Response(500, text="Internal Server Error")
        elif "healthy.example" in request.url.host:
            if request.url.path == "/robots.txt":
                return httpx.Response(404)
            return httpx.Response(
                200,
                headers={"Content-Type": "text/html"},
                text="<html><head><title>Healthy</title></head><body><h1>Healthy</h1></body></html>",
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        http_crawler = HttpCrawler(client=client)
        crawler = WebsiteCrawler(http_crawler=http_crawler, crawl_delay=0.0)
        service = CrawlerService(session=db_session, crawler=crawler)

        summary = await service.crawl_for_task(task.task_id)

    assert summary.total_websites == 2
    assert summary.websites_crawled == 1
    assert summary.failed_websites == 1
    assert summary.next_stage == "EXTRACTING"

    # Site 1 should be FAILED
    refreshed_broken = await db_session.get(Website, site_broken.id)
    assert refreshed_broken.status == "FAILED"

    # Site 2 should be CRAWLED
    refreshed_healthy = await db_session.get(Website, site_healthy.id)
    assert refreshed_healthy.status == "CRAWLED"

    # Task should remain active and advance to EXTRACTING
    refreshed_task = await db_session.get(ScrapingTask, task.id)
    assert refreshed_task.status == "RUNNING"
    assert refreshed_task.current_stage == "EXTRACTING"
    assert refreshed_task.websites_crawled == 1
    assert refreshed_task.failed_websites == 1


# ── 10. Idempotency Test ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_crawler_service_idempotency(db_session: AsyncSession) -> None:
    """Repeatedly crawling the same task updates existing SourcePages without duplicates."""
    user = User(
        name="Idempotent User",
        email="idempotent@example.com",
        password_hash="dummy_hash",
        role="USER",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id="TASK-000503",
        user_id=user.id,
        location="Puducherry",
        keyword="Schools",
    )
    db_session.add(task)
    await db_session.flush()

    org = Organization(name="Idempotent School", city="Puducherry")
    db_session.add(org)
    await db_session.flush()
    await db_session.execute(
        task_organizations.insert().values(task_id=task.id, organization_id=org.id)
    )

    web = Website(
        organization_id=org.id,
        url="https://idempotent.example",
        normalized_url="https://idempotent.example",
        domain="idempotent.example",
        status="PENDING",
    )
    db_session.add(web)
    await db_session.commit()

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "text/html"},
            text="<html><head><title>Version 1</title></head><body><p>Content</p></body></html>",
        )

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        http_crawler = HttpCrawler(client=client)
        crawler = WebsiteCrawler(http_crawler=http_crawler, crawl_delay=0.0)
        service = CrawlerService(session=db_session, crawler=crawler)

        # First run
        await service.crawl_for_task(task.task_id)

        # Second run
        await service.crawl_for_task(task.task_id)

    # Verify no duplicate SourcePages created
    stmt = select(SourcePage).where(SourcePage.website_id == web.id)
    res = await db_session.execute(stmt)
    pages = list(res.scalars().all())
    assert len(pages) == 1
    assert pages[0].page_title == "Version 1"


# ── 11. CLI Runner Output Format Test ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_crawl_cli_runner(db_session: AsyncSession, monkeypatch, capsys) -> None:
    from app.jobs.run_crawl import main as run_crawl_main
    from app.schemas.crawler import TaskCrawlSummary

    async def mock_run_crawl(task_id: str, session=None) -> TaskCrawlSummary:
        return TaskCrawlSummary(
            task_id=task_id,
            total_websites=2,
            websites_crawled=2,
            failed_websites=0,
            blocked_websites=0,
            total_pages_stored=12,
            playwright_total=0,
            duration_seconds=1.5,
            status="Crawling completed",
            next_stage="EXTRACTING",
        )

    monkeypatch.setattr("app.jobs.run_crawl.run_crawl", mock_run_crawl)
    monkeypatch.setattr("app.jobs.run_crawl.create_engine_and_factory", lambda: None)

    async def dummy_dispose():
        pass

    monkeypatch.setattr("app.jobs.run_crawl.dispose_engine", dummy_dispose)

    class MockContext:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("app.jobs.run_crawl.get_session_factory", lambda: lambda: MockContext())

    user = User(
        name="CLI User",
        email="cli@example.com",
        password_hash="dummy_hash",
        role="USER",
    )
    db_session.add(user)
    await db_session.flush()

    task = ScrapingTask(
        task_id="TASK-000504",
        user_id=user.id,
        location="Puducherry",
        keyword="Schools",
    )
    db_session.add(task)
    await db_session.commit()

    await run_crawl_main(task.task_id)

    captured = capsys.readouterr().out
    assert "Task: TASK-000504" in captured
    assert "Websites: 2" in captured
    assert "Crawled: 2" in captured
    assert "Failed: 0" in captured
    assert "Blocked: 0" in captured
    assert "Pages: 12" in captured
    assert "Playwright: 0" in captured
    assert "Status: Crawling completed" in captured
    assert "Next Stage: EXTRACTING" in captured

