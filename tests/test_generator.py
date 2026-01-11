from teleops.data_gen.generator import ScenarioConfig, generate_scenario


def test_generate_network_degradation_counts():
    config = ScenarioConfig(alert_rate_per_min=2, duration_min=3, noise_rate_per_min=1, seed=1)
    alerts, ground_truth = generate_scenario(config)

    # 2 incident alerts + 1 noise per minute
    assert len(alerts) == 3 * (2 + 1)
    assert ground_truth.incident_type == "network_degradation"
    assert "congestion" in ground_truth.root_cause
