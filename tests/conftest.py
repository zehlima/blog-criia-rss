"""Unit tests never inherit enabled operational switches from a runner."""
import pytest

@pytest.fixture(autouse=True)
def isolate_operational_switches(monkeypatch):
    monkeypatch.setenv('BORIS_DISCOVERY_ENABLED','0')
    monkeypatch.setenv('BORIS_DYNAMIC_INVENTORY','0')
