"""KREI 농업관측센터 과일 관측월보에서 사과 생산량·출하량 전망을 수집한다.

데이터 출처: https://aglook.krei.re.kr/main/uObserveMonth/OVR0000000013
사과 수치는 HTML이 아니라 매월 발간되는 PDF 관측월보 안에 있으므로
  1) monthList API로 연도별 월보 목록(PDF ID, 사과 페이지 위치)을 받고
  2) PDF를 내려받아(krei_pdfs/ 폴더에 캐시)
  3) 사과 페이지의 생산량·출하량·저장량 전망(추정) 표를 텍스트에서 파싱해
  4) 분석하기 쉬운 long 형식 CSV로 저장한다.

2020~2021년 대부분과 2024년 5~10월 월보는 글자가 텍스트가 아닌 도형으로
들어 있어 읽을 수 없다(OCR 필요). 이런 월보는 '표 없음'으로 건너뛴다.

필요 패키지: pip install pdfplumber

사용 예:
    python apple_krei_scraper.py                         # 최근 3개년
    python apple_krei_scraper.py --start 2020 --end 2026
    python apple_krei_scraper.py --out apple.csv
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime

import pdfplumber

BASE = "https://aglook.krei.re.kr/main/uObserveMonth/OVR0000000013"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0 Safari/537.36"
PDF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "krei_pdfs")

NUM = r"-?[\d,]+(?:\.\d+)?"
# 값은 단일 수치, 범위('1,369∼1,413'), 또는 '-'
VAL = rf"{NUM}(?:\s*[~∼]\s*{NUM})?|-"
VAL_RE = re.compile(VAL)
VALUES_RE = re.compile(rf"^(?:{VAL})(?:\s+(?:{VAL}))*$")
# 표의 행 이름: '2026년', '2025년산', '평년', '전년 대비', '평년 대비',
# 그리고 평년 비교가 없던 옛 월보의 '증감률'(= 전년 대비)
ROW_RE = re.compile(r"^(\d{4}년산?|전년\s*대비|평년\s*대비|평년|증감률)\s+(.+?)\s*$")
UNIT_RE = re.compile(r"단위\s*:\s*(.+)")
# 열 이름: '7월~익년 4월', '11월 이후', '내년 1월 이후', '햇사과(쓰가루, 썸머킹 등)',
# '전년 대비' 같이 공백이 든 이름을 한 덩어리로
LABEL = r"\d{4}년산?|전년\s*대비|평년\s*대비|평년"
COL_RE = re.compile(
    r"\d+월\s*[~∼]\s*(?:익년\s*)?\d+월(?:\s*이후)?|(?:내년|익년)\s*\d+월(?:\s*이후)?|\d+월\s*이후"
    rf"|{LABEL}|[^\s(]+\([^)]*\)|\S+"
)
LABEL_RE = re.compile(rf"^(?:{LABEL})$")
# 표 제목: '2026년 사과 생산량 전망', '6월 이후 사과 출하량 전망', '2023년산 사과 저장량 추정',
# '사과 출하량 증감률 (전년 대비)'
TITLE_RE = re.compile(r"사과\s*(생산량|출하량|저장량)\s*(?:전망|추정|증감률)")


def fetch(url, retries=2):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except OSError as e:
            if attempt == retries:
                raise
            print(f"  재시도 ({e})", file=sys.stderr)
            time.sleep(2)


def list_reports(year):
    """해당 연도에 발간된 과일 월보 목록."""
    data = json.loads(fetch(f"{BASE}/monthList?queryType={year}"))
    return [{
        "발간월": r["pub_YYYYMM"],
        "pdf_id": r["org_ID"],
        "파일명": r["orgtext_FILE_ORGNAME"],
        "bookmark": r.get("book_MARK") or "",
    } for r in data]


def apple_pages(bookmark, n_pages):
    """book_MARK('표지^1|사과^2|배^4|...')에서 사과 페이지 범위(0-based)를 구한다."""
    marks = []
    for part in bookmark.split("|"):
        name, _, page = part.partition("^")
        if page.isdigit():
            marks.append((name.strip(), int(page)))
    marks.sort(key=lambda m: m[1])
    for i, (name, page) in enumerate(marks):
        if name == "사과":
            end = marks[i + 1][1] - 1 if i + 1 < len(marks) else page + 1
            return range(page - 1, min(end, n_pages))
    return range(0, min(4, n_pages))  # 북마크가 없으면 앞쪽 페이지에서 찾는다


def download_pdf(report):
    os.makedirs(PDF_DIR, exist_ok=True)
    path = os.path.join(PDF_DIR, f"{report['발간월']}_{report['파일명']}")
    if not os.path.exists(path):
        data = fetch(f"{BASE}/download/{report['pdf_id']}/ORGTEXT_FILE")
        with open(path, "wb") as f:
            f.write(data)
        time.sleep(1)  # 서버 부담을 줄이기 위한 요청 간격
    return path


def parse_value(s):
    """'1,369∼1,413' → (중간값, 하한, 상한). 단일 값은 세 값이 같다."""
    if s == "-":
        return None, None, None
    nums = [float(n.replace(",", "")) for n in re.findall(NUM, s)]
    low, high = nums[0], nums[-1]
    return round((low + high) / 2, 3), low, high


def parse_table(title, item, lines, start):
    """lines[start]가 표 제목일 때, 그 아래 단위·헤더·데이터 행을 읽는다.

    item은 열 이름이 없는 표(행·열이 뒤집힌 표)에서 값의 항목 이름으로 쓴다.
    """
    header, sub_header, rows = [], "", []
    m = UNIT_RE.search(title)  # 옛 월보는 단위가 제목과 같은 줄에 있다
    unit = m.group(1).strip() if m else ""
    pre = []  # 단위 줄과 첫 값 줄 사이의 텍스트 줄들 (구분 열이 없는 표의 머리글)
    for line in lines[start + 1:start + 15]:
        line = line.strip()
        if line.startswith(("주:", "주 1)", "자료:", "※", "|")):
            break
        m = UNIT_RE.match(line)
        if m:
            unit = m.group(1).strip()
            continue
        if line.startswith("구분"):
            header = COL_RE.findall(line[2:])
            continue
        m = ROW_RE.match(line)
        if m and header and VALUES_RE.match(m.group(2)):
            values = VAL_RE.findall(m.group(2))
            cols = header
            # 두 줄짜리 헤더('9월 10월' 아래 '추석 성수기')는 첫 열 다음 열로 끼워 넣는다
            if sub_header and len(values) == len(header) + 1:
                cols = [header[0], sub_header] + header[1:]
            if len(values) == len(cols):
                label = "전년 대비" if m.group(1) == "증감률" else re.sub(r"\s+", " ", m.group(1))
                rows.append((label, list(zip(cols, values))))
            continue
        if VALUES_RE.match(line) and not header and pre:
            values = VAL_RE.findall(line)
            # 머리글 줄 중 행 이름('2023년산', '평년', '전년 대비')으로만 된 줄만 모은다
            labels = [c for p in pre if all(LABEL_RE.match(c) for c in COL_RE.findall(p))
                      for c in COL_RE.findall(p)]
            if labels and len(labels) == len(values):
                # 행·열이 뒤집힌 표: 머리글이 '2023년산 2022년산 평년 / 전년 대비 평년 대비'
                for label, value in zip(labels, values):
                    rows.append((re.sub(r"\s+", " ", label), [(item, value)]))
            else:
                # '구분' 열이 없는 표: 바로 윗줄이 열 이름, 이 줄이 값 (예: 전년 대비 % 표)
                cols = COL_RE.findall(pre[-1])
                if len(cols) == len(values):
                    # 7월호의 저장사과/햇사과 표는 제목에 '(전년 대비)'가 빠지기도 하지만 % 증감률이다
                    label = "전년 대비" if "전년 대비" in title or unit.strip() == "%" else "값"
                    rows.append((label, list(zip(cols, values))))
            continue
        if line == "증감률":
            continue
        if header and not rows:
            sub_header = line
        pre.append(line)
    return unit, rows


def extract_apple(pdf_path, bookmark):
    """사과 페이지에서 생산량·출하량·저장량 표를 찾아 long 형식 레코드로 돌려준다."""
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(pdf.pages[i].extract_text() or ""
                         for i in apple_pages(bookmark, len(pdf.pages)))
    lines = text.splitlines()

    records = []
    for i, line in enumerate(lines):
        m = TITLE_RE.search(line)
        if not m:
            continue
        table = m.group(1)
        # 제목 앞부분('6월 이후')이 있으면 뒤집힌 표의 항목 이름으로, 없으면 표 이름으로
        prefix = re.sub(rf"^[|I\s]+|{LABEL}", "", line[:m.start()]).strip()
        unit, rows = parse_table(line, prefix or table, lines, i)
        for row_name, cells in rows:
            is_rate = "대비" in row_name
            for col, raw in cells:
                col = re.sub(r"\s+", " ", col)
                col_unit = ""
                # 옛 월보는 단위가 열 이름에 붙어 있다: '재배면적(ha)', '생산량(천 톤)'
                m = re.match(r"^(.+?)\((ha|kg/10a|천\s*톤|톤)\)$", col)
                if m:
                    col, col_unit = m.group(1), m.group(2)
                value, low, high = parse_value(raw)
                records.append({
                    "표": table,
                    "구분": row_name,
                    "항목": col,
                    "값": value,
                    "하한": low,
                    "상한": high,
                    "원문": raw,
                    "단위": "%" if is_rate else (col_unit or unit_for(unit, col)),
                })
    return records


def unit_for(unit, col):
    """'ha, kg/10a, 천 톤, %' 처럼 묶인 단위를 열 이름에 맞춰 고른다."""
    parts = [u.strip() for u in unit.split(",")]
    if col == "재배면적" and "ha" in parts:
        return "ha"
    if col == "단수":
        return next((u for u in parts if "/10a" in u), unit)
    return next((u for u in parts if "톤" in u), unit)


def main():
    this_year = datetime.now().year
    parser = argparse.ArgumentParser(description="KREI 과일 관측월보 사과 생산량·출하량 스크래퍼")
    parser.add_argument("--start", type=int, default=this_year - 2, help="시작 연도")
    parser.add_argument("--end", type=int, default=this_year, help="끝 연도")
    parser.add_argument("--out", default="apple_production_shipment.csv", help="저장할 CSV 경로")
    args = parser.parse_args()

    out_rows, failed = [], []
    for year in range(args.start, args.end + 1):
        try:
            reports = list_reports(year)
        except OSError as e:
            print(f"[{year}] 목록 조회 실패: {e}", file=sys.stderr)
            continue
        for rep in sorted(reports, key=lambda r: r["발간월"]):
            print(f"[{rep['발간월']}] {rep['파일명']} 처리 중...", file=sys.stderr)
            try:
                records = extract_apple(download_pdf(rep), rep["bookmark"])
            except Exception as e:  # PDF 하나가 깨져도 나머지는 계속 수집
                print(f"  실패: {e}", file=sys.stderr)
                failed.append(rep["발간월"])
                continue
            if not records:
                print("  사과 생산량·출하량 표 없음", file=sys.stderr)
            for r in records:
                out_rows.append({"발간월": rep["발간월"], **r})

    if not out_rows:
        sys.exit("수집된 데이터가 없습니다.")

    fields = ["발간월", "표", "구분", "항목", "값", "하한", "상한", "원문", "단위"]
    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    months = sorted({r["발간월"] for r in out_rows})
    print(f"\n{len(months)}개 월보에서 {len(out_rows)}개 값 저장: {args.out}")
    if failed:
        print(f"처리 실패한 월보: {', '.join(failed)}")


if __name__ == "__main__":
    main()
