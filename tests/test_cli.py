from pathlib import Path

from dealbrief.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_writes_brief_to_output_file(tmp_path, capsys):
    out_file = tmp_path / "brief.md"
    exit_code = main([str(FIXTURES / "sample_notes.txt"), "--out", str(out_file)])

    assert exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "# Investment Brief: Acme Robotics" in content

    captured = capsys.readouterr()
    assert "Wrote brief" in captured.out


def test_cli_prints_to_stdout_when_no_out_flag_given(capsys):
    exit_code = main([str(FIXTURES / "sample_notes.txt")])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "# Investment Brief: Acme Robotics" in captured.out
