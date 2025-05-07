def test_cli():

    # Test the CLI help command
    import subprocess
    result = subprocess.run(['ti_plm', '--help'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'usage:' in result.stdout
    
def test_cli_display():
    # Test the CLI display command
    import subprocess
    result = subprocess.run(['ti_plm', 'display', '--help'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'usage:' in result.stdout
