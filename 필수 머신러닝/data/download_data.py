"""필수 머신러닝 실습 데이터 내려받기 (공개 데이터, 재배포 금지 대상 아님)

사용법:  python download_data.py
결과:    이 폴더(data/)에 노트북이 기대하는 파일 이름으로 저장됩니다.
         노트북은 data/ 안의 파일을 같은 폴더에서 읽도록 만들어져 있으므로,
         노트북을 실행할 때는 이 파일들을 노트북과 같은 폴더에 두거나
         아래 FILES 경로를 노트북 폴더로 지정하세요.

주의: online_retail_II.csv 는 원본 엑셀(xlsx)을 CSV로 바꾸면서 열 이름
      "Customer ID" 를 "CustomerID" 로 바꾼 파일입니다(노트북이 그 이름을 씁니다).
      wholesale.csv 는 원본의 "Delicassen" 을 "Delicatessen" 으로 바로잡았습니다.
"""
import io, os, zipfile, csv, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

def fetch(url, name):
    path = os.path.join(HERE, name)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        print("이미 있음:", name); return path
    print("내려받는 중:", url)
    urllib.request.urlretrieve(url, path)
    print("저장:", name, os.path.getsize(path), "bytes")
    return path

# 1) UCI Bank Marketing (45,211 × 17, 세미콜론 구분)
p = fetch("https://archive.ics.uci.edu/static/public/222/bank+marketing.zip", "bank.zip")
with zipfile.ZipFile(p) as z:
    z.extractall(HERE)
    inner = [n for n in z.namelist() if n.endswith("bank.zip")]
if inner:
    with zipfile.ZipFile(os.path.join(HERE, inner[0])) as z:
        z.extractall(HERE)
print("bank-full.csv 준비 완료")

# 2) IBM Telco Customer Churn (7,043 × 21)
fetch("https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv",
      "WA_Fn-UseC_-Telco-Customer-Churn.csv")

# 3) UCI Wholesale customers (440 × 8) — Delicassen → Delicatessen
p = fetch("https://archive.ics.uci.edu/static/public/292/wholesale+customers.zip", "wholesale.zip")
with zipfile.ZipFile(p) as z:
    z.extractall(HERE)
src = os.path.join(HERE, "Wholesale customers data.csv")
dst = os.path.join(HERE, "wholesale.csv")
with open(src, newline="", encoding="utf-8") as f, open(dst, "w", newline="", encoding="utf-8") as g:
    r, w = csv.reader(f), csv.writer(g)
    head = next(r); head = ["Delicatessen" if c == "Delicassen" else c for c in head]; w.writerow(head)
    for row in r: w.writerow(row)
print("wholesale.csv 준비 완료")

# 4) Online Retail II (1,067,371행) — xlsx → csv, Customer ID → CustomerID
p = fetch("https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip", "online_retail_ii.zip")
with zipfile.ZipFile(p) as z:
    z.extractall(HERE)
try:
    import openpyxl
except ImportError:
    raise SystemExit("Online Retail II 변환에는 openpyxl 이 필요합니다: pip install openpyxl")
import openpyxl
xlsx = os.path.join(HERE, "online_retail_II.xlsx")
out = os.path.join(HERE, "online_retail_II.csv")
wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); header_done = False
    for name in wb.sheetnames:
        for i, row in enumerate(wb[name].iter_rows(values_only=True)):
            if i == 0:
                if not header_done:
                    w.writerow(["CustomerID" if c == "Customer ID" else c for c in row]); header_done = True
                continue
            w.writerow(row)
wb.close()
print("online_retail_II.csv 준비 완료 (1,067,371행)")

# 5) Credit Card Fraud (284,807 × 31, 사기 492건) — TensorFlow 공개 미러
fetch("https://storage.googleapis.com/download.tensorflow.org/data/creditcard.csv", "creditcard.csv")
print("모든 데이터 준비 완료")
