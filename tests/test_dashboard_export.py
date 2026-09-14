from dashboard.export import ARTICLES_SQL, TRENDS_SQL


def test_dashboard_articles_are_limited_to_active_inventory():
    assert ARTICLES_SQL.count('rss_url=ANY(%s)') == 2


def test_dashboard_uses_only_complete_non_rejected_trend_runs():
    assert "count(DISTINCT scope)" in TRENDS_SQL
    assert "=3" in TRENDS_SQL
    assert "rejected_by_review" in TRENDS_SQL
