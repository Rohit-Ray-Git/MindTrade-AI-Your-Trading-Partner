# MindTrade AI - Your Trading Partner

An intelligent trading journal that combines structured trade data, psychology analysis, and AI-powered coaching to help traders improve their performance.

## Features

- **Trade Management**: Import fills from Delta Exchange + manual entries
- **Psychology Tracking**: Capture emotional states and behavioral patterns
- **AI Analysis**: Multi-agent system for pattern detection and coaching
- **Analytics Dashboard**: Comprehensive P&L, risk metrics, and performance insights
- **Automated Coaching**: Personalized recommendations based on trading patterns

## Architecture

```
├── agents/           # AI agent implementations
├── orchestrator/     # Agent orchestration logic
├── ui/              # Streamlit dashboard
├── api/             # FastAPI backend
├── models/          # Database models
├── utils/           # Helper utilities
└── docker/          # Containerization
```

## Quick Start

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Delta Exchange API credentials

### Local Development

1. **Clone and setup environment**:
```bash
git clone <repository-url>
cd mindtrade-ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your Delta API credentials
```

3. **Start services**:
```bash
docker-compose up -d
```

4. **Access applications**:
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- API Docs: http://localhost:8000/docs

### Production Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## API Endpoints

### Trades
- `POST /api/trades` - Create new trade
- `GET /api/trades` - List trades with filters
- `GET /api/trades/{id}` - Get specific trade

### Analytics
- `GET /api/analytics/summary` - Basic metrics
- `GET /api/analytics/setup-performance` - Setup-wise analysis
- `GET /api/analytics/psychology` - Psychology insights

### Delta Integration
- `POST /api/sync/delta` - Import fills from Delta Exchange

## Development Phases

- **Phase 0**: Project scaffold ✅
- **Phase 1**: Data model + manual journal MVP
- **Phase 2**: Basic analytics + rule heuristics
- **Phase 3**: Delta Exchange integration
- **Phase 4**: Multi-agent AI system
- **Phase 5**: Advanced models & automation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details
