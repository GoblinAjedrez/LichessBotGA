name: Lichess Bot Runner

concurrency:
  group: lichess-bot-runner
  cancel-in-progress: true

on:
  workflow_dispatch:
  schedule:
    - cron: '0 */6 * * *'

jobs:
  bot-runner:
    runs-on: ubuntu-latest
    timeout-minutes: 355

    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install system packages
        run: |
          sudo apt-get update
          sudo apt-get install -y stockfish

      - name: Install Python dependencies
        run: |
          python3 -m pip install --upgrade pip setuptools wheel
          python3 -m pip install -r requirements.txt
          python3 -m pip install tenacity pyyaml

      - name: Prepare engines
        run: |
          mkdir -p engines
          STOCKFISH_BIN="$(command -v stockfish)"
          if [ -z "$STOCKFISH_BIN" ]; then
            echo "ERROR: stockfish no encontrado"
            exit 1
          fi

          cp "$STOCKFISH_BIN" engines/stockfish
          cp "$STOCKFISH_BIN" engines/fsf-latest
          cp "$STOCKFISH_BIN" engines/fsf

          chmod +x engines/stockfish
          chmod +x engines/fsf-latest
          chmod +x engines/fsf

          echo "Motores preparados:"
          ls -l engines/

      - name: Inject token into config
        env:
          LICHESS_TOKEN: ${{ secrets.LICHESS_TOKEN }}
        run: |
          if [ -z "$LICHESS_TOKEN" ]; then
            echo "ERROR: falta el secret LICHESS_TOKEN"
            exit 1
          fi

          python3 << 'EOF'
          import os
          import yaml

          with open("config.yml", "r", encoding="utf-8") as f:
              config = yaml.safe_load(f) or {}

          config["token"] = os.environ["LICHESS_TOKEN"]

          with open("config.yml", "w", encoding="utf-8") as f:
              yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

          print("Token metido correctamente en config.yml")
          EOF

      - name: Sanity check
        run: |
          python3 -c "import tenacity, yaml; print('Python OK')"
          test -f engines/stockfish && echo "stockfish OK"
          test -f engines/fsf-latest && echo "fsf-latest OK"
          test -f engines/fsf && echo "fsf OK"

      - name: Run bot
        run: |
          python3 user_interface.py
