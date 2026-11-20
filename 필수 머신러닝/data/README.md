# 실습 데이터 안내

노트북은 아래 파일을 **노트북과 같은 폴더**에서 읽습니다. 저장소에는 용량 때문에 원본을 넣지 않았습니다.
`python download_data.py` 를 실행하면 이 폴더에 노트북이 기대하는 이름으로 준비됩니다.
노트북은 같은 폴더의 CSV를 읽으므로, 실행할 때는 **이 폴더의 파일을 노트북이 있는 폴더(`../모듈실습/`, `../퀘스트/`)로 복사**하거나, 노트북과 데이터를 같은 임시 폴더에 두고 실행하세요.

| 파일 | 원본 | 행 × 열 | 노트북이 기대하는 형태 | 라이선스 |
| --- | --- | --- | --- | --- |
| `bank-full.csv` | [UCI Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing) (`bank.zip` 안) | 45,211 × 17 | 세미콜론 구분 (`sep=";"`), `df.shape == (45211, 17)` | CC BY 4.0 (UCI) |
| `WA_Fn-UseC_-Telco-Customer-Churn.csv` | [IBM Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) | 7,043 × 21 | `df.shape == (7043, 21)` | IBM 공개 샘플 데이터 |
| `online_retail_II.csv` | [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) | 1,067,371 × 8 | 엑셀 두 시트를 합쳐 CSV로 변환, `Customer ID` → `CustomerID` | CC BY 4.0 (UCI) |
| `wholesale.csv` | [UCI Wholesale customers](https://archive.ics.uci.edu/dataset/292/wholesale+customers) | 440 × 8 | 원본의 `Delicassen` 을 `Delicatessen` 으로 바로잡음 | CC BY 4.0 (UCI) |
| `creditcard.csv` | [ULB MLG Credit Card Fraud](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) (공개 미러: TensorFlow) | 284,807 × 31 (사기 492건) | `Class` 열 = 사기 여부 | ULB MLG / Kaggle |

## 실행 환경

- Python 3.12, pandas 3.1.1, numpy 2.5.4, scikit-learn 1.9.1, shap 0.54.1, mlxtend 0.25.0, matplotlib 3.11.2
- 노트북 첫 부분의 `[환경]` 셀이 `fonts/NanumGothic-Regular.ttf` 를 등록해 그래프의 한글을 표시합니다. (저장소의 `fonts/` 는 상위 폴더에 있습니다.)
- 실행: `jupyter nbconvert --to notebook --execute --inplace <노트북>.ipynb`

## 재현 시 확인할 값 (교안과 같은 숫자가 나오는지)

| 확인 | 기대값 |
| --- | --- |
| `bank-full.csv` | `(45211, 17)`, 가입률 11.7% |
| Telco | `(7043, 21)`, 해지율 26.5% |
| Online Retail II 정제 후 | 805,549행, 고객 5,878명, 군집 대상 4,266명 |
| creditcard | 284,807행, 사기 492건 (0.173%) |
| wholesale | 440행, 소매점 298 / 호텔·식당 142 |
