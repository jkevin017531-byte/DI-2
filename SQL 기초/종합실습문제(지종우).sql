-- ═══════════════════════════════════════
-- 종합실습문제 — 조건별 주문 조회 쿼리 모음
-- ═══════════════════════════════════════

-- 질문 1. 2023년 11월에 들어온 주문의 주문번호·주문일·상태·금액
-- 결과: 6행 (O0013~O0018)
SELECT order_id, order_date, status, amount
FROM `my-project-jkevin72`.modul.orders
WHERE order_date BETWEEN '2023-11-01' AND '2023-11-30';

-- 질문 2. 금액이 입력된 주문 중 20만 원 초과 고액 주문
-- 결과: 6행
SELECT order_id, order_date, status, amount
FROM `my-project-jkevin72`.modul.orders
WHERE amount IS NOT NULL
  AND amount > 200000;

-- 질문 3. 결제 완료(Paid) 또는 배송 완료(Shipped) 주문 — 시각화용 데이터
-- 결과: 21행 (Paid 13 + Shipped 8)
SELECT order_id, order_date, status, amount
FROM `my-project-jkevin72`.modul.orders
WHERE status IN ('Paid', 'Shipped');
