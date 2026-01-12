from teleops.data_gen.generator import ScenarioConfig, generate_scenario


def test_generate_network_degradation_counts():
    config = ScenarioConfig(alert_rate_per_min=2, duration_min=3, noise_rate_per_min=1, seed=1)
    alerts, ground_truth = generate_scenario(config)

    # 2 incident alerts + 1 noise per minute
    assert len(alerts) == 3 * (2 + 1)
    assert ground_truth.incident_type == "network_degradation"
    assert "congestion" in ground_truth.root_cause


def test_generate_dns_outage():
    config = ScenarioConfig(incident_type="dns_outage", alert_rate_per_min=2, duration_min=2, noise_rate_per_min=0, seed=2)
    alerts, ground_truth = generate_scenario(config)
    assert len(alerts) == 4
    assert ground_truth.incident_type == "dns_outage"
    assert "DNS" in ground_truth.root_cause


def test_generate_unknown_scenario():
    config = ScenarioConfig(incident_type="unsupported")
    try:
        generate_scenario(config)
    except ValueError as exc:
        assert "Unsupported incident type" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported scenario")
