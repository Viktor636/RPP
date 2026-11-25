# lab-5 — лабораторная работа №5

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

## Проверка

- API: http://localhost:8000/docs
- Notifier: http://localhost:8001/stats
- Analytics: http://localhost:8002/stats
- RabbitMQ: http://localhost:15672

## Примеры операций

Покупка:
```bash
curl -X POST http://localhost:8000/operations \
  -H "Content-Type: application/json" \
  -d '{"operation_id":"S12-K03-000154","type":"purchase","customer_id":"C1042","store_id":"S12","check_number":"S12-000154","amount":"2490.00","occurred_at":"2026-11-10T14:32:05+07:00"}'
```

Возврат:
```bash
curl -X POST http://localhost:8000/operations \
  -H "Content-Type: application/json" \
  -d '{"operation_id":"S12-K03-000155","type":"return","customer_id":"C1042","store_id":"S12","check_number":"S12-000154","occurred_at":"2026-11-10T15:00:00+07:00"}'
```

Оплата баллами:
```bash
curl -X POST http://localhost:8000/operations \
  -H "Content-Type: application/json" \
  -d '{"operation_id":"S12-K03-000156","type":"redeem","customer_id":"C1042","store_id":"S12","check_number":"S12-000156","amount":"1000.00","points":200,"occurred_at":"2026-11-10T16:00:00+07:00"}'
```

Результат:
```bash
curl http://localhost:8000/operations/S12-K03-000154
curl http://localhost:8000/accounts/C1042
curl "http://localhost:8001/notifications?customer_id=C1042"
curl http://localhost:8002/stores/S12
```