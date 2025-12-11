"""
Standardized test logger for molecule/pytest tests.

Usage:
    from automation_library.testing import TestLogger
    
    log = TestLogger("Verify container exists")
    log.check("Checking file...")
    log.passed("File exists", "Path: /etc/file")
"""

# Global storage for last test output
_last_output = ""


def get_test_output(test_name: str = None) -> str:
    """Get captured output for the last test."""
    return _last_output


class OmniaLogger:
    """Standardized test output logger."""
    
    def __init__(self, test_name: str):
        global _last_output
        self.test_name = test_name
        self._output_lines = []
        self._add_line(f"{'='*70}")
        self._add_line(f"  {test_name}")
        self._add_line(f"{'='*70}")
    
    def _add_line(self, line: str):
        """Add line to output and print."""
        global _last_output
        self._output_lines.append(line)
        print(line)
        _last_output = "\n".join(self._output_lines)
    
    def check(self, message: str):
        """Log check being performed."""
        self._add_line(f"  → {message}")
    
    def passed(self, message: str, details: str = None):
        """Log passed result."""
        self._add_line(f"  ✔ PASS: {message}")
        if details:
            for line in details.split('\n'):
                self._add_line(f"    │ {line}")
    
    def failed(self, message: str, details: str = None):
        """Log failed result."""
        self._add_line(f"  ✘ FAIL: {message}")
        if details:
            for line in details.split('\n'):
                self._add_line(f"    │ {line}")
    
    def get_output(self) -> str:
        """Get all captured output."""
        return "\n".join(self._output_lines)
