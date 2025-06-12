#!/bin/bash
"""
Skrypt do uruchomienia testów weryfikacji agenta.
"""

echo "🔍 Uruchamianie testów weryfikacji agenta AI..."

# Uruchomienie testów jednostkowych
echo "📋 Testy jednostkowych narzędzi..."
python -m pytest tests/test_simple_math.py tests/test_task_manager.py -v

# Uruchomienie testów weryfikacji agenta
echo "🤖 Testy systemu agentowego..."
python -m pytest test_agent_verification.py -v

# Uruchomienie testów integracyjnych (jeśli istnieją)
echo "🔗 Testy integracyjne..."
python -m pytest tests/ -k "integration" -v

echo "✅ Wszystkie testy zakończone!"
