#!/usr/bin/env bash
# Run this once to set up the project
python3 -m venv venv
source venv/bin/activate      # Mac/Linux
# .\venv\Scripts\activate     # Windows (uncomment this line instead)
pip install -r requirements.txt
echo "Setup complete. To run the game:"
echo "  source venv/bin/activate"
echo "  python main.py"
