-- ═════════════════════════════════════════════
-- 시각화 실습 - 종합실습문제(데이터로 차트 만들기)
-- ═════════════════════════════════════════════

-- 차트 1. 주문별 금액 (막대 / 측정기준 order_id / 측정항목 amount)

SELECT order_id, amount
FROM `my-project-jkevin72`.modul.orders
WHERE status IN ('Paid', 'Shipped');

-- 차트 2. 상태별 주문 건수 (막대 / 측정기준 status / 측정항목 order_count)

SELECT status, COUNT(*) AS order_count
FROM `my-project-jkevin72`.modul.orders
WHERE status IN ('Paid', 'Shipped')
GROUP BY status;

-- 질문 3. 차트 3. 월별 매출 추이 (선 / 측정기준 order_month / 측정항목 sales)

SELECT
  FORMAT_DATE('%Y-%m', order_date) AS order_month,
  SUM(amount) AS sales
FROM `my-project-jkevin72`.modul.orders
WHERE status IN ('Paid', 'Shipped')
GROUP BY order_month
ORDER BY order_month;
