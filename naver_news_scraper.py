"""네이버 뉴스 섹션별 헤드라인 스크래퍼.

네이버 뉴스 각 섹션 페이지(https://news.naver.com/section/<id>)의
헤드라인 기사를 수집해 CSV로 저장한다. 표준 라이브러리만 사용한다.

사용 예:
    python naver_news_scraper.py                      # 전체 섹션, 섹션당 3개
    python naver_news_scraper.py --top 5              # 섹션당 5개
    python naver_news_scraper.py --sections 101 105   # 경제, IT/과학만
    python naver_news_scraper.py --out news.csv
"""

import argparse
import csv
import html
import re
import sys
import time
import urllib.request
from datetime import datetime

SECTIONS = {
    "100": "정치",
    "101": "경제",
    "102": "사회",
    "103": "생활/문화",
    "104": "세계",
    "105": "IT/과학",
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

# 헤드라인 기사 하나는 <li class="sa_item _SECTION_HEADLINE"> 블록 하나에 들어 있다.
ITEM_RE = re.compile(r'<li class="sa_item _SECTION_HEADLINE.*?</li>', re.S)
TITLE_RE = re.compile(
    r'<a href="([^"]+)"[^>]*class="sa_text_title[^"]*"[^>]*>\s*'
    r'<strong class="sa_text_strong">(.*?)</strong>',
    re.S,
)
LEDE_RE = re.compile(r'class="sa_text_lede">(.*?)</div>', re.S)
PRESS_RE = re.compile(r'class="sa_text_press">(.*?)</div>', re.S)
CLUSTER_RE = re.compile(r'class="sa_text_cluster_num">(\d+)<', re.S)


def clean(text):
    """태그를 지우고 HTML 엔티티와 공백을 정리한다."""
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def fetch(url, retries=2):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except OSError as e:
            if attempt == retries:
                raise
            print(f"  재시도 ({e})", file=sys.stderr)
            time.sleep(1)


def parse_headlines(page):
    articles = []
    for block in ITEM_RE.findall(page):
        title = TITLE_RE.search(block)
        if not title:
            continue
        lede = LEDE_RE.search(block)
        press = PRESS_RE.search(block)
        cluster = CLUSTER_RE.search(block)
        articles.append({
            "제목": clean(title.group(2)),
            "언론사": clean(press.group(1)) if press else "",
            "요약": clean(lede.group(1)) if lede else "",
            "관련기사수": int(cluster.group(1)) if cluster else 0,
            "링크": html.unescape(title.group(1)),
        })
    return articles


def scrape(section_ids, top):
    rows = []
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    for sid in section_ids:
        name = SECTIONS[sid]
        print(f"[{name}] 수집 중...", file=sys.stderr)
        try:
            page = fetch(f"https://news.naver.com/section/{sid}")
        except OSError as e:
            print(f"  실패: {e}", file=sys.stderr)
            continue
        articles = parse_headlines(page)[:top]
        if not articles:
            print("  기사를 찾지 못했습니다 (페이지 구조 변경 가능성).", file=sys.stderr)
        for rank, art in enumerate(articles, 1):
            rows.append({"섹션": name, "순위": rank, **art, "수집시각": collected_at})
        time.sleep(0.5)  # 서버 부담을 줄이기 위한 요청 간격
    return rows


def save_csv(rows, path):
    fields = ["섹션", "순위", "제목", "언론사", "요약", "관련기사수", "링크", "수집시각"]
    # utf-8-sig: 엑셀에서 열어도 한글이 깨지지 않도록 BOM 포함
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="네이버 뉴스 섹션별 헤드라인 스크래퍼")
    parser.add_argument("--sections", nargs="+", choices=SECTIONS.keys(),
                        default=list(SECTIONS), help="섹션 ID (기본: 전체)")
    parser.add_argument("--top", type=int, default=3, help="섹션당 기사 수 (기본: 3)")
    parser.add_argument("--out", default=f"naver_news_{datetime.now():%Y%m%d_%H%M}.csv",
                        help="저장할 CSV 경로")
    args = parser.parse_args()

    rows = scrape(args.sections, args.top)
    if not rows:
        sys.exit("수집된 기사가 없습니다.")
    save_csv(rows, args.out)

    for r in rows:
        print(f"[{r['섹션']}] {r['순위']}. {r['제목']} ({r['언론사']})")
    print(f"\n총 {len(rows)}개 기사 저장 완료: {args.out}")


if __name__ == "__main__":
    main()
