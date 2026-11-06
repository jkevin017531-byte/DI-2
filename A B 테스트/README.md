\# 마케팅 캠페인 A/B 테스트 분석



광고(ad)와 공익광고(psa)를 본 사용자의 구매 전환율을 비교해, 광고 캠페인을 계속 운영할지 판단한 분석입니다.



\## 주요 결과



\- 광고 그룹의 전환율이 공익광고 그룹보다 높았습니다 (2.55% vs 1.79%).

\- +0.77%p \[95% CI +0.60, +0.94], 1.43배 \[95% CI 1.30, 1.58], χ²(1) = 54.32, p < .001

\- 결정: 광고 캠페인 계속 운영 (손익분기 조건 확인 필요)



\## 파일



| 파일 | 내용 |

| --- | --- |

| `marketing\_ab\_test.ipynb` | 분석 노트북 (데이터 점검 → 가설 → 검정 → 결과 → 세그먼트 → 의사결정) |

| `marketing\_AB.csv` | 분석 데이터 |



\## 데이터 출처



\[Marketing A/B Testing (Kaggle)](https://www.kaggle.com/datasets/faviovaz/marketing-ab-testing)



\## 실행 방법



1\. `marketing\_AB.csv`를 노트북과 같은 폴더에 둡니다.

2\. 노트북을 열고 \*\*Restart → Run All\*\*로 처음부터 실행합니다.



필요한 라이브러리: `numpy`, `pandas`, `matplotlib`, `seaborn`, `scipy` (1.11 이상)

