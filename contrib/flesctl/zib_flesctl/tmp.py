
"""Usage:
  myprogram.py --time=<timestamp>

Options:
  --time=<timestamp>   A human-readable time string.
"""

from docopt import docopt
from dateutil import parser
from datetime import datetime

if __name__ == '__main__':
    args = docopt(__doc__)
    time_str = args['--time']

    try:
        parsed_time = parser.parse(time_str)
        print(f"Parsed datetime: {parsed_time.isoformat()}")
    except (ValueError, TypeError) as e:
        print(f"Could not parse time: {e}")
# Parsed from string
input_time = parser.parse("2024-05-16 13:45")

# Current time
now = datetime.now()

# Comparison
if parsed_time > now:
    print("The input time is in the future.")
else:
    print("The input time is in the past.")
