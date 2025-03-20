# Nasdaq Stock Screener

A Python-based Nasdaq Stock Screener with a Tkinter GUI that evaluates 47 custom conditions on simulated IBKR OHLC data. This application allows you to upload a ticker list (up to 50 tickers), select a screening date, enable/disable individual screening conditions, and then run the screener to display and save the results.

## Features

- **Graphical User Interface:** Built with Tkinter for easy use.
- **Ticker List Upload:** Load a list of tickers from a text file (one ticker per line, maximum of 50 tickers).
- **Date Selection:** Choose a screening date (default is set to the last trading day).
- **Simulated Data Retrieval:** Retrieves simulated OHLC data (Open, High, Low, Close) for each ticker over a specified time period.
- **47 Screening Conditions:** Evaluate stocks against 47 predefined conditions (with the ability to enable/disable each condition individually).
- **Results Display:** View matching tickers with their order number and the Open price from the 16:00 bar of the previous day.
- **Results Saving:** Save the screening results to a text file (`screener_results.txt`).

## Requirements

- Python 3.x
- Modules: `tkinter`, `pandas`, `numpy`

*(Note: Tkinter is usually included with Python on most systems.)*

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/NadirAliOfficial/Nasdaq-Stock-Screener
   ```

2. **Navigate to the project directory:**

   ```bash
   cd nasdaq-stock-screener
   ```

3. **(Optional) Create a virtual environment and install dependencies:**

   ```bash
   python -m venv venv
   source venv/bin/activate   # For Linux/macOS
   venv\Scripts\activate      # For Windows
   pip install -r requirements.txt
   ```

   *If you don't have a `requirements.txt`, you can manually install pandas and numpy:*

   ```bash
   pip install pandas numpy
   ```

## Usage

1. **Run the application:**

   ```bash
   python script.py
   ```

2. **Using the Application:**
   - **Screening Date:** Enter a screening date in the format `YYYY-MM-DD` (default is set automatically).
   - **Upload Ticker List:** Click on "Upload Ticker List" to select a text file containing your tickers.
   - **Select Conditions:** Use the scrollable list of 47 conditions to enable or disable specific checks.
   - **Run Screener:** Click on "Run Screener" to evaluate the tickers. Matching stocks will appear in the results table and will also be saved to `screener_results.txt`.
   - **Reset:** Click on "Reset" to clear the current settings and results.

## File Structure

- `script.py` – Main application file containing the GUI and logic.
- `screener_results.txt` – Output file where the screening results are saved.
- `README.md` – This file.

## Contributing

Contributions are welcome! If you have suggestions or improvements, please feel free to fork the repository and submit a pull request.



