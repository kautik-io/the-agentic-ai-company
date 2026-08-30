# Deployment

## Docker Compose (Development)

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed.py
```

## Production Checklist

- [ ] Set strong `SECRET_KEY` in environment
- [ ] Use managed PostgreSQL (RDS, Cloud SQL)
- [ ] Use managed Redis (ElastiCache, Memorystore)
- [ ] Configure HTTPS reverse proxy (nginx/Caddy)
- [ ] Set `CORS_ORIGINS` to production domain
- [ ] Enable rate limiting
- [ ] Configure AI provider API keys via secrets manager
- [ ] Set up CI/CD (GitHub Actions included in Phase 13)
- [ ] Configure monitoring (logs, metrics, alerts)
- [ ] Back up PostgreSQL regularly

## Environment Variables

See `.env.example` for all configuration options.

## Scaling

- **API**: Horizontal scaling behind load balancer
- **Workers**: Scale Celery workers for agent execution
- **WebSocket**: Redis pub/sub for cross-instance event broadcast
- **Database**: Read replicas for analytics queries

## Kubernetes (Optional)

Kubernetes manifests planned for Phase 13. Docker Compose is sufficient for initial production.
