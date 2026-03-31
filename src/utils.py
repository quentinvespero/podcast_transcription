from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


# Query parameters that carry no content identity (tracking / sharing tokens)
_STRIP_PARAMS = {
    "si",           # YouTube sharing token
    "feature",      # YouTube feature tracking
    "pp",           # YouTube Shorts / preview
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
}


def normalize_url(url: str) -> str:
    """
    Return a canonical form of *url* by stripping known junk/tracking parameters.

    Content-identifying parameters (e.g. YouTube's `v=`, `list=`, `t=`) are
    preserved. Remaining parameters are sorted so that parameter-order differences
    don't create phantom duplicates.

    Non-YouTube URLs pass through unchanged (the stripped set is harmless on them).
    """
    parsed  = urlparse(url)
    params  = parse_qs(parsed.query, keep_blank_values=True)
    cleaned = {k: v for k, v in params.items() if k not in _STRIP_PARAMS}
    # Sort keys for a stable canonical form
    new_query = urlencode(sorted(cleaned.items()), doseq=True)
    return urlunparse(parsed._replace(query=new_query))
