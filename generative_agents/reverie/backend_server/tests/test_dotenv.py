import os

import utils


def test_load_dotenv_sets_unset_vars(tmp_path):
    p = tmp_path / ".env"
    p.write_text('SMALLDESIRE_TEST_VAR=hello\n# a comment\nQUOTED="q val"\n')
    os.environ.pop("SMALLDESIRE_TEST_VAR", None)
    os.environ.pop("QUOTED", None)
    utils._load_dotenv(str(p))
    assert os.environ["SMALLDESIRE_TEST_VAR"] == "hello"
    assert os.environ["QUOTED"] == "q val"
    del os.environ["SMALLDESIRE_TEST_VAR"]
    del os.environ["QUOTED"]


def test_load_dotenv_does_not_override(tmp_path):
    p = tmp_path / ".env"
    p.write_text("SMALLDESIRE_TEST_VAR2=fromfile\n")
    os.environ["SMALLDESIRE_TEST_VAR2"] = "preset"
    utils._load_dotenv(str(p))
    assert os.environ["SMALLDESIRE_TEST_VAR2"] == "preset"  # setdefault: not overridden
    del os.environ["SMALLDESIRE_TEST_VAR2"]


def test_load_dotenv_missing_file_is_noop(tmp_path):
    utils._load_dotenv(str(tmp_path / "does_not_exist.env"))  # must not raise
