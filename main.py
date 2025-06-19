import pytz
import logging
import datetime
import pandas as pd
import tkinter as tk

from ib_insync import IB, Stock, util
from pandas.tseries.offsets import BDay 
from tkinter import ttk, filedialog, messagebox

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

eastern = pytz.timezone("US/Eastern")

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

logger.info("Connected to IB Gateway/TWS")

def extract_comparator(condition_text):

    for symbol in ["≥", "≤", "≠", "=", ">", "<"]:

        if symbol in condition_text:
            return symbol
        
    return "?"

def inverse_comparator(text):

    inversions = {"≥": "<", 
                  "≤": ">", 
                  "=": "≠", 
                  "≠": "=", 
                  ">": "≤", 
                  "<": "≥"}
    
    return text.translate(str.maketrans(inversions)) if any(k in text for k in inversions) else f"Inverse de ({text})"

class StockScreenerApp:

# region : Setup functions

    def __init__(self, root):

        self.root = root
        self.root.title("Nasdaq Stock Screener")

        self.tickers = []
        self.ticker_vars = {}

        self.ohlc_data = {}
        self.conditions = {}

        self.results = []  
        self.create_widgets()
        self.setup_conditions()
    
    def create_widgets(self):

        # style = ttk.Style(self.root)
        # style.configure("SmallIndicator.TCheckbutton", font=("Arial", 11))

        self.main_frame = ttk.Frame(self.root, padding=5)
        self.main_frame.grid(row=0, column=0, sticky=tk.NSEW)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        #
        # Controls Frame (row=0, col=0)
        #

        control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding=5)
        control_frame.grid(row=0, column=0, sticky=tk.NW, padx=5, pady=5)

        ttk.Label(control_frame, text="Screening Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W)

        self.date_entry = ttk.Entry(control_frame, width=12)
        self.date_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.date_entry.insert(0, self.get_default_date().strftime("%Y-%m-%d"))

        ttk.Button(control_frame, text="Upload Ticker List", command=self.upload_file).grid(row=1, column=0, columnspan=2, pady=5)

        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Button(btn_frame, text="Run Screener", command=self.run_screener).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)

        #
        # Results Frame (row=1, col=0) => directly below the Controls
        #

        results_frame = ttk.LabelFrame(self.main_frame, text="Results", padding=5)
        results_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)

        self.tree = ttk.Treeview(results_frame, columns=("result",), show="headings")
        self.tree.heading("result", text="Results")
        self.tree.pack(fill=tk.BOTH, expand=True)

        #
        # Indicators Frame (row=0, col=1, rowspan=2) => spans rows 0 & 1 on the right
        #

        indicators_frame = ttk.LabelFrame(self.main_frame, text="Indicators", padding=5)
        indicators_frame.grid(row=0, column=1, rowspan=2, sticky=tk.NSEW, padx=5, pady=5)
        self.cond_scrollable = ttk.Frame(indicators_frame)
        self.cond_scrollable.pack(fill=tk.BOTH, expand=True)

        deselect_btn = ttk.Button(self.cond_scrollable, text="Deselect All Indicators", command=self.deselect_all_conditions)
        deselect_btn.pack(pady=0)

        #
        # Ticker Selection Frame 
        #

        self.ticker_frame = ttk.LabelFrame(self.main_frame, text="Ticker Selection", padding=5)
        self.ticker_frame.grid(row=0, column=2, rowspan=2, sticky=tk.NSEW, padx=5, pady=5)
        self.ticker_inner_frame = ttk.Frame(self.ticker_frame)
        self.ticker_inner_frame.pack(fill=tk.BOTH, expand=True)

        ticker_btn_frame = ttk.Frame(self.ticker_frame)
        ticker_btn_frame.pack(pady=5)

        ttk.Button(ticker_btn_frame, text="Select All", command=self.select_all_tickers).pack(side=tk.LEFT, padx=2)
        ttk.Button(ticker_btn_frame, text="Unselect All", command=self.unselect_all_tickers).pack(side=tk.LEFT, padx=2)

        #
        # Configure row/column weights
        #

        self.main_frame.rowconfigure(0, weight=0)
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.columnconfigure(0, weight=0)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.columnconfigure(2, weight=1)

    def setup_conditions(self):

        cond_defs = [
                    (1, "Close 18h DAY-1 ≥ Open 18h DAY-1"), (2, "Close 19h DAY-1 ≥ Open 19h DAY-1"),(3, "Close 4h ≥ Open 4h"), (4, "Close 5h ≥ Open 5h"), (5, "Close 6h ≥ Open 6h"),
                    (6, "Close 7h ≥ Open 7h"), (7, "Close 8h ≥ Open 8h"), (8, "Close 9h ≥ Open 9h"), (9, "Close 10h ≥ Open 10h"), (10, "Close 11h ≥ Open 11h"), 
                    (11, "Close 12h ≥ Open 12h"), (12, "Close 13h ≥ Open 13h"), (13, "Close 14h ≥ Open 14h"), (14, "Close 15h ≥ Open 15h"), (15, "Close 16h ≥ Open 16h"), 
                    (16, "Close 17h ≥ Open 17h"), (17, "Close 18h ≥ Open 18h"), (18, "Close 19h ≥ Open 19h"), (19, "Low 4h ≤ Low 19h DAY-1"), (20, "Low 5h ≤ Low 4h"), 
                    (21, "Low 6h ≤ Low 5h"), (22, "Low 7h ≤ Low 6h"), (23, "Low 8h ≤ Low 7h"), (24, "Low 9h ≤ Low 8h"), (25, "Low 10h ≤ Low 9h"), 
                    (26, "Low 11h ≤ Low 10h"), (27, "Low 12h ≤ Low 11h"), (28, "Low 13h ≤ Low 12h"), (29, "Low 14h ≤ Low 13h"), (30, "Low 15h ≤ Low 14h"),
                    (31, "Low 16h ≤ Low 15h"), (32, "Low 17h ≤ Low 16h"), (33, "Low 18h ≤ Low 17h"), (34, "Low 19h ≤ Low 18h"), (35, "High 4h ≥ High [4;15]"), 
                    (36, "High 5h ≥ High [4;15]"), (37, "High 6h ≥ High [4;15]"), (38, "High 7h ≥ High [4;15]"), (39, "High 8h ≥ High [4;15]"), (40, "High 9h ≥ High [4;15]"),
                    (41, "High 10h ≥ High [4;15]"), (42, "High 11h ≥ High [4;15]"), (43, "High 12h ≥ High [4;15]"), (44, "High 13h ≥ High [4;15]"), (45, "High 14h ≥ High [4;15]"), 
                    (46, "High 15h ≥ High [4;15]"), (47, "High 16h ≥ High [4;19]"), (48, "High 17h ≥ High [4;19]"), (49, "High 18h ≥ High [4;19]"), (50, "High 19h ≥ High [4;19]"),
                    (51, "High 4h ≥ High 19h DAY-1"), (52, "High 5h ≥ High 4h"), (53, "High 6h ≥ High 5h"), (54, "High 7h ≥ High 6h"), (55, "High 8h ≥ High 7h"), 
                    (56, "High 9h ≥ High 8h"), (57, "High 10h ≥ High 9h"), (58, "High 11h ≥ High 10h"), (59, "High 12h ≥ High 11h"), (60, "High 13h ≥ High 12h"), 
                    (61, "High 14h ≥ High 13h"), (62, "High 15h ≥ High 14h"), (63, "High 16h ≥ High 15h"), (64, "High 17h ≥ High 16h"), (65, "High 18h ≥ High 17h"),
                    (66, "High 19h ≥ High 18h"), (67, "High 10h > High [4;9]"), (68, "Low 10h < Low [4;9]"), (69, "Open 4h ≠ Low 4h"), (70, "Open 4h ≠ High 4h"), 
                    (71, "Close 4h ≠ Low 4h"), (72, "Close 4h ≠ High 4h"), (73, "Open 5h ≠ Low 5h"), (74, "Open 5h ≠ High 5h"), (75, "Close 5h ≠ Low 5h"), 
                    (76, "Close 5h ≠ High 5h"), (77, "First bar : Close ≥ Open"), (78, "Second bar : Close ≥ Open"), (79, "Third bar : Close ≥ Open"), (80, "Low First bar ≤ Low 19h DAY-1"), 
                    (81, "Low Second bar ≤ Low First bar"), (82, "High 4h ≥ High [5;8]"), (83, "High 8h ≥ High [4;7]"), (84, "High 18h DAY-1 ≠ Low 18h DAY-1"), (85, "High 19h DAY-1 ≠ Low 19h DAY-1"),
                    (86, "High 4h ≠ Low 4h"), (87, "High 5h ≠ Low 5h"), (88, "High 6h ≠ Low 6h"), (89, "High 7h ≠ Low 7h"), (90, "High 8h ≠ Low 8h"), 
                    (91, "High 9h ≠ Low 9h"), (92, "High 10h ≠ Low 10h"), (93, "High 11h ≠ Low 11h"), (94, "High 12h ≠ Low 12h"),
                    (95, "High 13h ≠ Low 13h"), (96, "High 14h ≠ Low 14h"), (97, "High 15h ≠ Low 15h"), (98, "High 16h ≠ Low 16h"), (99, "High 17h ≠ Low 17h"), (100, "High 18h ≠ Low 18h"),
                    (101, "High 19h ≠ Low 19h"), (102, "First bar = 4h"), (103, "First bar = 5h"), (104, "First bar = 6h"), (105, "First bar = 7h"), 
                    (106, "First bar = 8h"), (107, "First bar = 9h"), (108, "Open 16h = Low 16h"), (109, "Open 17h = Low 17h"), (110, "Open 18h = Low 18h"),
                    (111, "Open 19h = Low 19h"), (112, "Open 16h = High 16h"), (113, "Open 17h = High 17h"), (114, "Open 18h = High 18h"), (115, "Open 19h = High 19h"),
                    (116, "Close 16h = Low 16h"), (117, "Close 17h = Low 17h"), (118, "Close 18h = Low 18h"), (119, "Close 19h = Low 19h"), (120, "Close 16h = High 16h"), 
                    (121, "Close 17h = High 17h"), (122, "Close 18h = High 18h"), (123, "Close 19h = High 19h"), (124, "High [16h DAY-1 ; 19h DAY] > 1.5 * Open 16h DAY-1"), (125, "High [16h DAY-1 ; 19h DAY] > 1.7 * Open 16h DAY-1"),
                    (126, "High [4h DAY ; 19h DAY] > 2 * Close 19h DAY-1")]

        notebook = ttk.Notebook(self.cond_scrollable)
        notebook.pack(fill=tk.BOTH, expand=True)

        tab1 = ttk.Frame(notebook)
        tab2 = ttk.Frame(notebook)
        notebook.add(tab1, text="Conditions 1 –> 101")
        notebook.add(tab2, text="Conditions 102 –> 126")

        def create_grid_conditions(tab, start_idx, end_idx):

            chunk_size = 34
            large_font = ("Arial", 9)

            style = ttk.Style()
            style.configure("Large.TLabel", font=large_font)
            style.configure("Large.TCheckbutton", font=large_font)

            for block_start in range(start_idx, end_idx, chunk_size):

                block_end = min(block_start + chunk_size, end_idx)
                block_idx = (block_start - start_idx) // chunk_size

                block_frame = ttk.LabelFrame(tab, text=f"Conditions {cond_defs[block_start][0]} – {cond_defs[block_end - 1][0]}")
                block_frame.grid(row=0, column=block_idx, padx=10, pady=10, sticky="n")

                for i in range(block_start, block_end):

                    idx, label = cond_defs[i]
                    row = i - block_start

                    comparator = extract_comparator(label)
                    opposite_comparator = inverse_comparator(comparator)

                    lbl = ttk.Label(block_frame, text=f"{idx}. {label}", anchor="w", style="Large.TLabel")
                    lbl.grid(row=row, column=0, sticky="w")

                    # ✔️ Label
                    tick_icon = ttk.Label(block_frame, text=f"{comparator}")
                    tick_icon.grid(row=row, column=1, sticky="e", padx=(5, 2))

                    var = tk.BooleanVar()
                    chk = ttk.Checkbutton(block_frame, variable=var, style="Large.TCheckbutton")
                    chk.grid(row=row, column=2, sticky="w")

                    # ❌ Label
                    cross_icon = ttk.Label(block_frame, text=f"{opposite_comparator}")
                    cross_icon.grid(row=row, column=3, sticky="e", padx=(10, 2))

                    inv_var = tk.BooleanVar()
                    inv_chk = ttk.Checkbutton(block_frame, variable=inv_var, style="Large.TCheckbutton")
                    inv_chk.grid(row=row, column=4, sticky="w")

                    self.conditions[str(idx)] = var
                    self.conditions[f"inv_{idx}"] = inv_var

                    def make_callback(main=var, inverse=inv_var):

                        def callback(*args):

                            if main.get():
                                inverse.set(False)
                                
                            elif inverse.get():
                                main.set(False)

                        return callback

                    var.trace_add("write", make_callback(var, inv_var))
                    inv_var.trace_add("write", make_callback(inv_var, var))

        create_grid_conditions(tab1, 0, 101)
        create_grid_conditions(tab2, 101, len(cond_defs))
               
# endregion

# region : Useful functions

    def reset(self):

        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, self.get_default_date().strftime("%Y-%m-%d"))

        self.tickers = []

        self.ticker_vars = {}
        self.ohlc_data = {}
        self.results = []

        self.tree.delete(*self.tree.get_children())

        for var in self.conditions.values():
            var.set(False)

        for widget in self.ticker_inner_frame.winfo_children():
            widget.destroy()

        logger.info("Application reset.")

    def upload_file(self):

        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])

        if path:

            try:
                with open(path, "r") as f:
                    content = f.read().strip()

                tickers = [x.strip() for x in content.split(",") if x.strip()]
                tickers = [ticker.split(":")[-1] for ticker in tickers]

                if len(tickers) > 50:
                    messagebox.showerror("Error", "Maximum 50 tickers allowed")
                    return
                
                self.tickers = tickers
                messagebox.showinfo("Success", f"Loaded {len(tickers)} tickers:\n{', '.join(tickers)}")

                logger.info(f"Tickers loaded: {', '.join(tickers)}")
                self.populate_ticker_selection()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                logger.error(f"Error loading file: {e}")
 
    def save_results(self):

        with open("output/screener_results.txt", "w") as f:

            f.write("Serial\tTickerNo\tTicker\tOpen16hDay-1\n")

            for serial, ticker_no, ticker, open_val in sorted(self.results, key=lambda x: x[0]):
                f.write(f"{serial}\t{ticker_no}\t{ticker}\t{open_val}\n")

        logger.info("Results saved to screener_results.txt")
    
    def run_screener(self):

        self.tree.delete(*self.tree.get_children())

        try:
            screening_date = datetime.datetime.strptime(self.date_entry.get(), "%Y-%m-%d").date()

        except ValueError:
            messagebox.showerror("Error", "Invalid date format (YYYY-MM-DD)")
            return

        self.ohlc_data, self.results = {}, []
        selected_tickers = [t for t, var in self.ticker_vars.items() if var.get()]
        logger.info(f"Running screener for date {screening_date} on tickers: {selected_tickers}")

        for ticker in selected_tickers:

            logger.info(f"Fetching data for {ticker}")
            df = self.fetch_data(ticker, screening_date - datetime.timedelta(days=2), screening_date)

            if df.empty or not isinstance(df.index, pd.DatetimeIndex):
                logger.warning(f"Data empty or index invalid for {ticker}, skipping.")
                continue

            self.ohlc_data[ticker] = df

            data_day_minus1 = None
            day_cursor = screening_date - datetime.timedelta(days=1)

            for _ in range(7):  

                temp = df[df.index.date == day_cursor]

                if not temp.empty:
                    
                    data_day_minus1 = temp
                    break

                day_cursor -= datetime.timedelta(days=1)

            data = df[df.index.date == screening_date]

            if data_day_minus1.empty or data.empty:
                logger.info(f"No data for {ticker} on screening date or previous day. Skipping ticker.")
                continue

            open_16h = self.find_previous_16h_open(df, screening_date)

            if open_16h is None:

                logger.info(f"No valid 16:00 bar found for {ticker} within ~7 days before {screening_date}. Skipping ticker.")
                continue

            logger.info(f"For {ticker}, Open16hDay-1 is taken as {open_16h}")

            if self.evaluate_conditions(data, open_16h, data_day_minus1):

                ticker_no = self.tickers.index(ticker) + 1 if ticker in self.tickers else 0
                serial = len(self.results) + 1

                self.results.append((serial, ticker_no, ticker, open_16h))

        for serial, ticker_no, ticker, open_val in self.results:

            result_str = f"{serial}. TickerNo:{ticker_no} - {ticker} - Open16h: {open_val}"
            self.tree.insert("", "end", values=(result_str,))

        self.save_results()

        messagebox.showinfo("Success", f"Found {len(self.results)} matches.\nResults saved to screener_results.txt")
        logger.info(f"Screener finished with {len(self.results)} matches.")

    def deselect_all_conditions(self):

        for key, var in self.conditions.items():

            if not key.startswith("inv_") and key.isdigit():
                var.set(False)

            elif key.startswith("inv_"):
                var.set(False)

        logger.info("All indicator checkboxes deselected.")

# endregion

# region : Ticker functions
     
    def populate_ticker_selection(self):

        for widget in self.ticker_inner_frame.winfo_children():
            widget.destroy()

        self.ticker_vars = {}

        for i, ticker in enumerate(self.tickers, start=1):

            var = tk.BooleanVar(value=True)
            row = (i - 1) % 25
            col = (i - 1) // 25

            ttk.Checkbutton(self.ticker_inner_frame, text=f"{i}. {ticker}", variable=var).grid(row=row, column=col, sticky=tk.W)
            self.ticker_vars[ticker] = var

    def select_all_tickers(self):

        for var in self.ticker_vars.values():
            var.set(True)

    def unselect_all_tickers(self):

        for var in self.ticker_vars.values():
            var.set(False)
    
# endregion

# region : Data functions

    def fetch_data(self, ticker, day_minus1, day):

        """
        Fetch extended hours data over 7 days to cover weekends/holidays.
        """

        try:
            contract = Stock(ticker, "SMART", "USD")
            ib.qualifyContracts(contract)

            target_datetime = datetime.datetime.combine(day, datetime.time(23, 59))
            localized_dt = eastern.localize(target_datetime).astimezone(pytz.utc)
            end_time_str = localized_dt.strftime("%Y%m%d %H:%M:%S")

            logger.info(f"Fetching data for {ticker} with end time {end_time_str} (US/Eastern, extended hours)")
            
            bars = ib.reqHistoricalData(contract,
                                        endDateTime=end_time_str,
                                        durationStr="7 D",
                                        barSizeSetting="1 hour",
                                        whatToShow="TRADES",
                                        useRTH=False,
                                        formatDate=1)
            
            if not bars:
                logger.warning(f"No data returned for {ticker}")
                return pd.DataFrame()
            
            df = util.df(bars)
            df["date"] = pd.to_datetime(df["date"])

            df.set_index("date", inplace=True)

            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC").tz_convert("US/Eastern")

            else:
                df.index = df.index.tz_convert("US/Eastern")

            df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"}, inplace=True)
            logger.info(f"Data for {ticker} covers timestamps: {df.index.tolist()}")
            df.to_csv(f"output/{ticker}_raw_data.csv")

            logger.info(f"Raw data for {ticker} saved to {ticker}_raw_data.csv")
            return df
        
        except Exception as e:

            logger.error(f"Error fetching {ticker}: {e}")
            return pd.DataFrame()

    def get_default_date(self):
         
        now = datetime.datetime.now(eastern)

        default_date = (now + BDay(1)).date() if now.time() > datetime.time(20, 0) else now.date()
        logger.info(f"Default screening date set to: {default_date}")

        return default_date

    def evaluate_conditions(self, data, open_16h_day_minus1, data_day_minus1=None):

        results = {}

        def get_bar(df, h):

            rtn = df.between_time(f"{int(h):02d}:00", f"{int(h):02d}:59")

            if rtn.empty:
                return None
            
            row = rtn.iloc[-1]
            
            if isinstance(row, pd.DataFrame):
                row = row.squeeze()

            return row

        def get_range_high(df, start_h, end_h):

            bars = [get_bar(df, h) for h in range(start_h, end_h + 1)]
            highs = [bar["High"] for bar in bars if bar is not None]
            return max(highs) if highs else None

        def get_range_low(df, start_h, end_h):

            bars = [get_bar(df, h) for h in range(start_h, end_h + 1)]
            lows = [bar["Low"] for bar in bars if bar is not None]
            return min(lows) if lows else None

        def check(cid, cond):

            primary = self.conditions.get(str(cid), None)
            inverse = self.conditions.get(f"inv_{cid}", None)

            try:
                
                if isinstance(cond, pd.Series):

                    if cond.size == 1:
                        cond = cond.item()

                    else:
                        raise ValueError(f"Condition {cid} is ambiguous Series with multiple values: {cond}")
                    
                cond_bool = bool(cond)

            except Exception as e:
                logger.error(f"Error evaluating condition {cid}: {e} | cond={cond}")
                cond_bool = False

            if primary and primary.get():
                results[cid] = cond_bool

            elif inverse and inverse.get():
                results[cid] = not cond_bool

        try:

            # Conditions 1-2 (Jour J-1)
            if data_day_minus1 is not None:
                bar_18_yest = get_bar(data_day_minus1, 18)
                bar_19_yest = get_bar(data_day_minus1, 19)
                check(1, bar_18_yest is not None and bar_18_yest["Close"] >= bar_18_yest["Open"])
                check(2, bar_19_yest is not None and bar_19_yest["Close"] >= bar_19_yest["Open"])

            # Conditions 3-18 (Close >= Open)
            for cid, hour in zip(range(3, 19), range(4, 20)):
                bar = get_bar(data, hour)
                check(cid, bar is not None and bar["Close"] >= bar["Open"])

            # Condition 19 (Low 4h <= Low 19h DAY-1)
            if data_day_minus1 is not None:
                low_4h = get_bar(data, 4)
                low_19_yest = get_bar(data_day_minus1, 19)
                check(19, low_4h is not None and low_19_yest is not None and low_4h["Low"] <= low_19_yest["Low"])

            # Conditions 20-34 (Low i <= Low i-1)
            for cid, hour in zip(range(20, 35), range(5, 20)):
                bar = get_bar(data, hour)
                prev_bar = get_bar(data, hour - 1)
                check(cid, bar is not None and prev_bar is not None and bar["Low"] <= prev_bar["Low"])

            # Conditions 35-46 (High i >= High 4–15)
            max_4_15 = get_range_high(data, 4, 15)
            for cid, hour in zip(range(35, 47), range(4, 16)):
                bar = get_bar(data, hour)
                check(cid, bar is not None and max_4_15 is not None and bar["High"] >= max_4_15)

            # Conditions 47-50 (High i >= High 4–19)
            max_4_19 = get_range_high(data, 4, 19)
            for cid, hour in zip(range(47, 51), range(16, 20)):
                bar = get_bar(data, hour)
                check(cid, bar is not None and max_4_19 is not None and bar["High"] >= max_4_19)

            # Condition 51 (High 4h >= High 19h DAY-1)
            if data_day_minus1 is not None:
                bar_4h = get_bar(data, 4)
                bar_19_yest = get_bar(data_day_minus1, 19)
                check(51, bar_4h is not None and bar_19_yest is not None and bar_4h["High"] >= bar_19_yest["High"])

            # Conditions 52–66 (High i >= High i-1)
            for cid, hour in zip(range(52, 67), range(5, 20)):
                bar = get_bar(data, hour)
                prev_bar = get_bar(data, hour - 1)
                check(cid, bar is not None and prev_bar is not None and bar["High"] >= prev_bar["High"])

            # Condition 67 (High 10h > High [4–9])
            max_4_9 = get_range_high(data, 4, 9)
            bar_10h = get_bar(data, 10)
            check(67, bar_10h is not None and max_4_9 is not None and bar_10h["High"] > max_4_9)

            # Condition 68 (Low 10h < Low [4–9])
            min_4_9 = get_range_low(data, 4, 9)
            check(68, bar_10h is not None and min_4_9 is not None and bar_10h["Low"] < min_4_9)

            # Conditions 69–76 (Open/Close ≠ High/Low for 4h/5h)
            for cid, hour in zip(range(69, 77), [4, 4, 4, 4, 5, 5, 5, 5]):

                bar = get_bar(data, hour)

                if bar is not None:

                    if cid % 4 == 1:
                        check(cid, bar["Open"] != bar["Low"])
                    elif cid % 4 == 2:
                        check(cid, bar["Open"] != bar["High"])
                    elif cid % 4 == 3:
                        check(cid, bar["Close"] != bar["Low"])
                    elif cid % 4 == 0:
                        check(cid, bar["Close"] != bar["High"])

            # Conditions 77–79 (First/Second/Third bars Close ≥ Open)
            for cid, hour in zip(range(77, 80), [4, 5, 6]):
                bar = get_bar(data, hour)
                check(cid, bar is not None and bar["Close"] >= bar["Open"])

            # Conditions 80–81 (Low bar ≤ Low previous bar)
            bar_19_yest = get_bar(data_day_minus1, 19) if data_day_minus1 is not None else None

            bar_4 = get_bar(data, 4)
            bar_5 = get_bar(data, 5)

            check(80, bar_4 is not None and bar_19_yest is not None and bar_4["Low"] <= bar_19_yest["Low"])
            check(81, bar_5 is not None and bar_4 is not None and bar_5["Low"] <= bar_4["Low"])

            # Conditions 82–83 (High comparisons in short ranges)
            max_5_8 = get_range_high(data, 5, 8)
            bar_4 = get_bar(data, 4)

            check(82, bar_4 is not None and max_5_8 is not None and bar_4["High"] >= max_5_8)

            max_4_7 = get_range_high(data, 4, 7)
            bar_8 = get_bar(data, 8)

            check(83, bar_8 is not None and max_4_7 is not None and bar_8["High"] >= max_4_7)

            # Conditions 84–85 (High ≠ Low for DAY-1 18h/19h)
            if data_day_minus1 is not None:

                bar_18_yest = get_bar(data_day_minus1, 18)
                bar_19_yest = get_bar(data_day_minus1, 19)
                check(84, bar_18_yest is not None and bar_18_yest["High"] != bar_18_yest["Low"])
                check(85, bar_19_yest is not None and bar_19_yest["High"] != bar_19_yest["Low"])

            # Conditions 86–101 (High ≠ Low from 4h to 19h)
            for cid, hour in zip(range(86, 102), range(4, 20)):
                bar = get_bar(data, hour)
                check(cid, bar is not None and bar["High"] != bar["Low"])

            # Conditions 102–107: First bar = 4h to 9h
            first_bar_hour = None

            for h in range(4, 10):
                bar = get_bar(data, h)
                if bar is not None:
                    first_bar_hour = h
                    break 

            for cid in range(102, 108):
                check(cid, False)

            if first_bar_hour:
                cid = 102 + (first_bar_hour - 4) 
                check(cid, True)

            # Conditions 108–111 (Open = Low)
            for cid, hour in zip(range(108, 112), range(16, 20)):
                bar = get_bar(data, hour)
                check(cid, bar is not None and bar["Open"] == bar["Low"])

            # Conditions 112–115 (Open = High)
            for cid, hour in zip(range(112, 116), range(16, 20)):
                bar = get_bar(data, hour)
                check(cid, bar is not None and bar["Open"] == bar["High"])

            # Conditions 116–119 (Close = Low)
            for cid, hour in zip(range(116, 120), range(16, 20)):
                bar = get_bar(data, hour)
                check(cid, bar is not None and bar["Close"] == bar["Low"])

            # Conditions 120–123 (Close = High)
            for cid, hour in zip(range(120, 124), range(16, 20)):
                bar = get_bar(data, hour)
                check(cid, bar is not None and bar["Close"] == bar["High"])

            # Condition 124–125: High from 16h Y-1 to 19h D > x * open_16h_day_minus1
            if data_day_minus1 is not None and open_16h_day_minus1:

                highs = []

                for h in range(16, 20):
                    bar = get_bar(data_day_minus1, h)

                    if bar is not None:
                        highs.append(bar["High"])

                for h in range(4, 20):
                    bar = get_bar(data, h)
                    
                    if bar is not None:
                        highs.append(bar["High"])
                if highs:
                    max_high = max(highs)
                    check(124, max_high > 1.5 * open_16h_day_minus1)
                    check(125, max_high > 1.7 * open_16h_day_minus1)

            # Condition 126: High 4h–19h > 2 * Close 19h DAY-1
            if data_day_minus1 is not None:
                bar_19_yest = get_bar(data_day_minus1, 19)
                max_high_today = get_range_high(data, 4, 19)
                check(126, bar_19_yest is not None and max_high_today is not None and max_high_today > 2 * bar_19_yest["Close"])

            logger.info("Final condition results: %s", results)
            return all(results.values())

        except Exception as e:
            
            logger.error("Error evaluating conditions: %s", e)
            return False
        
    def find_previous_16h_open(self, df, screening_date):

        """
        Look back from the day before screening_date up to 7 days.
        For each day, return the latest bar between 16:00 and 23:59 (US/Eastern).
        """

        day_cursor = screening_date - datetime.timedelta(days=1)

        for _ in range(7):

            day_data = df[df.index.date == day_cursor]

            if not day_data.empty:
               
                candidate_bar = day_data.between_time("16:00", "16:00")

                if not candidate_bar.empty:

                    latest_bar = candidate_bar.iloc[-1]
                    open_16h = latest_bar["Open"]

                    logger.info(f"Found bar for {day_cursor} at {latest_bar.name.strftime('%H:%M')}, open={open_16h}")
                    return open_16h
                
            day_cursor -= datetime.timedelta(days=1)

        logger.warning(f"No 16:00+ bar found in last 7 days before {screening_date}")
        return None
    
# endregion

if __name__ == "__main__":

    root = tk.Tk()
    root.state("zoomed")
    root.attributes("-fullscreen", True)

    try:
        root.iconbitmap("money_analyze_icon_143358.ico")
        
    except Exception as e:
        print("Error setting icon with iconbitmap:", e)
        
    app = StockScreenerApp(root)
    root.mainloop()
