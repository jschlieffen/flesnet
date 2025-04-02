
"""
Usage:
  my_program.py <param1> <param2>
  
Options:
  <param1>  First string parameter with or without spaces.
  <param2>  Second string parameter with or without spaces.
"""
from docopt import docopt

def main():
    arguments = docopt(__doc__)
    param1 = arguments["<param1>"]
    param2 = arguments["<param2>"]
    
    print(f"Received param1: {param1}")
    print(f"Received param2: {param2}")

if __name__ == "__main__":
    main()
