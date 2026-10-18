import json

import pytest

from resume_analyzer.config import Config, ConfigError, load_config


def test_defaults_normalised():
    cfg = Config().validate()
    assert sum(cfg.weights.values()) == pytest.approx(1.0)


def test_load_from_file_and_env(tmp_path):
    f = tmp_path / "c.json"
    f.write_text(json.dumps({"output_dir": "a", "strong_threshold": 80}))
    cfg = load_config(str(f), env={"RESUME_ANALYZER_OUTPUT_DIR": "b"})
    assert cfg.output_dir == "b" and cfg.strong_threshold == 80


def test_env_log_level():
    assert load_config(env={"RESUME_ANALYZER_LOG_LEVEL": "debug"}).log_level == "DEBUG"


def test_weights_rescaled():
    cfg = Config(weights={"skills": 2, "experience": 1, "education": 1, "keywords": 0}).validate()
    assert cfg.weights["skills"] == 0.5


@pytest.mark.parametrize("bad", [
    {"weights": {"skills": 1}},
    {"weights": {"skills": -1, "experience": 1, "education": 1, "keywords": 1}},
    {"weights": {"skills": 0, "experience": 0, "education": 0, "keywords": 0}},
    {"strong_threshold": 10, "maybe_threshold": 50},
])
def test_invalid_config(bad):
    with pytest.raises(ConfigError):
        Config(**bad).validate()


def test_unknown_key_and_missing_and_bad_json(tmp_path):
    f = tmp_path / "c.json"
    f.write_text('{"nope": 1}')
    with pytest.raises(ConfigError):
        load_config(str(f), env={})
    with pytest.raises(ConfigError):
        load_config(str(tmp_path / "missing.json"), env={})
    f.write_text("{bad")
    with pytest.raises(ConfigError):
        load_config(str(f), env={})
