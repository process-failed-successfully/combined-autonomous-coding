import io
from unittest.mock import patch
from shared.csv2sql_lab import Csv2SqlManager, run_csv2sql_lab_logic


def test_csv2sql_manager_convert_valid_csv():
    manager = Csv2SqlManager()
    csv_data = "id,name\n1,Alice\n2,Bob O'Reilly\n"
    sql = manager.convert(csv_data, "users")

    assert "INSERT INTO users (id, name) VALUES ('1', 'Alice');" in sql
    assert "INSERT INTO users (id, name) VALUES ('2', 'Bob O''Reilly');" in sql


def test_csv2sql_manager_empty_csv():
    manager = Csv2SqlManager()
    sql = manager.convert("", "users")
    assert sql == ""

    sql2 = manager.convert("   \n  ", "users")
    assert sql2 == ""


def test_csv2sql_manager_no_headers():
    manager = Csv2SqlManager()
    sql = manager.convert(",,,", "users")
    assert sql == ""


def test_csv2sql_manager_missing_headers():
    manager = Csv2SqlManager()

    # We trigger the StopIteration branch by overriding io.StringIO
    with patch('csv.reader', side_effect=lambda x: iter([])):
        sql = manager.convert("id,name", "users")
        assert sql == ""


def test_csv2sql_manager_empty_headers_list():
    manager = Csv2SqlManager()

    with patch('csv.reader', side_effect=lambda x: iter([[]])):
        sql = manager.convert("id,name", "users")
        assert sql == ""


def test_csv2sql_manager_no_rows():
    manager = Csv2SqlManager()
    sql = manager.convert("id,name\n", "users")
    assert sql == ""


def test_csv2sql_manager_empty_rows():
    manager = Csv2SqlManager()
    sql = manager.convert("id,name\n\n\n1,Alice\n", "users")
    assert "INSERT INTO users (id, name) VALUES ('1', 'Alice');" in sql


def test_csv2sql_manager_uneven_rows():
    manager = Csv2SqlManager()
    csv_data = "id,name\n1\n2,Bob,Extra\n"
    sql = manager.convert(csv_data, "users")

    assert "INSERT INTO users (id, name) VALUES ('1', '');" in sql
    assert "INSERT INTO users (id, name) VALUES ('2', 'Bob');" in sql


def test_run_csv2sql_lab_logic_cli_text():
    class Args:
        text = "id,name\n1,Alice"
        file = None
        table = "test_table"
        output = None

    args = Args()

    with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
        success = run_csv2sql_lab_logic(args)
        assert success is True
        output = mock_stdout.getvalue()
        assert "INSERT INTO test_table (id, name) VALUES ('1', 'Alice');" in output


def test_run_csv2sql_lab_logic_cli_file(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("col1,col2\nval1,val2")

    class Args:
        text = None
        file = str(csv_file)
        table = "test_table"
        output = None

    args = Args()

    with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
        success = run_csv2sql_lab_logic(args)
        assert success is True
        output = mock_stdout.getvalue()
        assert "INSERT INTO test_table (col1, col2) VALUES ('val1', 'val2');" in output


def test_run_csv2sql_lab_logic_cli_output_file(tmp_path):
    class Args:
        text = "col1,col2\nval1,val2"
        file = None
        table = "test_table"
        output = str(tmp_path / "out.sql")

    args = Args()

    with patch('sys.stdout', new_callable=io.StringIO):
        success = run_csv2sql_lab_logic(args)
        assert success is True

    out_content = (tmp_path / "out.sql").read_text()
    assert "INSERT INTO test_table (col1, col2) VALUES ('val1', 'val2');" in out_content


def test_run_csv2sql_lab_logic_cli_stdin():
    class Args:
        text = None
        file = None
        table = "test_table"
        output = None

    args = Args()

    with patch('sys.stdin', io.StringIO("a,b\n1,2")), patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
        success = run_csv2sql_lab_logic(args)
        assert success is True
        assert "INSERT INTO test_table (a, b) VALUES ('1', '2');" in mock_stdout.getvalue()


def test_run_csv2sql_lab_logic_file_error():
    class Args:
        text = None
        file = "/path/to/nonexistent/file.csv"
        table = "test_table"
        output = None

    args = Args()
    with patch('sys.stderr', new_callable=io.StringIO):
        success = run_csv2sql_lab_logic(args)
        assert success is False


def test_run_csv2sql_lab_logic_stdin_error():
    class Args:
        text = None
        file = None
        table = "test_table"
        output = None

    args = Args()
    with patch('sys.stdin.read', side_effect=Exception("Stdin Error")), patch('sys.stderr', new_callable=io.StringIO):
        success = run_csv2sql_lab_logic(args)
        assert success is False


def test_run_csv2sql_lab_logic_conversion_error():
    class Args:
        text = "id,name\n1,Alice"
        file = None
        table = "test_table"
        output = None

    args = Args()

    with patch('shared.csv2sql_lab.Csv2SqlManager.convert', side_effect=Exception("Mock Error")), patch('sys.stderr', new_callable=io.StringIO):
        success = run_csv2sql_lab_logic(args)
        assert success is False
