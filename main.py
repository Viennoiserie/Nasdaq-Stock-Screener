import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import pandas as pd
import numpy as np
from pandas.tseries.offsets import BDay

class StockScreenerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nasdaq Stock Screener")
        
        # Data storage
        self.tickers = []
        self.ohlc_data = {}
        self.conditions = {}
        self.results = []
        
        # Create UI components
        self.create_widgets()
        self.setup_conditions()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: Controls
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        control_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)
        
        # Date selection
        ttk.Label(control_frame, text="Screening Date:").grid(row=0, column=0, sticky=tk.W)
        self.date_entry = ttk.Entry(control_frame)
        self.date_entry.grid(row=0, column=1, sticky=tk.EW)
        self.date_entry.insert(0, self.get_default_date().strftime("%Y-%m-%d"))
        
        # File upload button
        ttk.Button(control_frame, text="Upload Ticker List", command=self.upload_file).grid(row=1, column=0, columnspan=2, pady=5)
        
        # Conditions frame
        cond_frame = ttk.LabelFrame(main_frame, text="Conditions", padding=10)
        cond_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=5)
        
        # Scrollable canvas for conditions
        canvas = tk.Canvas(cond_frame, borderwidth=0)
        scrollbar = ttk.Scrollbar(cond_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons (Run and Reset)
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Run Screener", command=self.run_screener).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
        
        self.tree = ttk.Treeview(results_frame, columns=("Num", "Ticker", "Open"), show="headings")
        self.tree.heading("Num", text="Number")
        self.tree.heading("Ticker", text="Ticker")
        self.tree.heading("Open", text="Open 16h DAY-1")
        self.tree.pack(fill=tk.BOTH, expand=True)
        
    def setup_conditions(self):
        # Define all 47 conditions with their description.
        condition_defs = [
            (1, "Close 5h ≥ Open 5h"),
            (2, "Close 6h ≥ Open 6h"),
            (3, "Close 7h ≥ Open 7h"),
            (4, "Close 8h ≥ Open 8h"),
            (5, "Close 9h ≥ Open 9h"),
            (6, "Close 10h ≥ Open 10h"),
            (7, "Close 11h ≥ Open 11h"),
            (8, "Close 12h ≥ Open 12h"),
            (9, "Close 13h ≥ Open 13h"),
            (10, "Close 15h ≥ Open 15h"),
            (11, "Close 16h ≥ Open 16h"),
            (12, "Close 17h ≥ Open 17h"),
            (13, "Close 18h ≥ Open 18h"),
            (14, "Close 19h ≥ Open 19h"),
            (15, "High 15h ≠ Low 15h"),
            (16, "High 16h ≠ Low 16h"),
            (17, "High 17h ≠ Low 17h"),
            (18, "High 18h ≠ Low 18h"),
            (19, "High 19h ≠ Low 19h"),
            (20, "Open 18h = Low 18h"),
            (21, "Close 18h ≠ High 18h"),
            (22, "High [4h ; 20h] = High [10h ; 15h]"),
            (23, "Close 18h < Open 18h"),
            (24, "Open 18h ≠ High 18h"),
            (25, "Close 18h = Low 18h"),
            (26, "High 18h = Low 18h"),
            (27, "High [4h ; 20h] = High [10h ; 20h]"),
            (28, "Close 10h < Open 10h"),
            (29, "High 10h ≥ High 9h"),
            (30, "Low 10h ≥ Low 9h"),
            (31, "Low 17h ≤ Low 16h"),
            (32, "Open 17h = Low 17h"),
            (33, "Open 18h = High 18h"),
            (34, "Close 18h ≠ Low 18h"),
            (35, "Close 19h > Low 16h"),
            (36, "Low 19h > Low 16h"),
            (37, "Low 19h > Low 17h"),
            (38, "Low 19h > Low 18h"),
            (39, "Open 16h = Low 16h"),
            (40, "Open 16h = High 16h"),
            (41, "Close < Open and High in [4h ; 20h]"),
            (42, "Close ≥ Open and High in [4h ; 20h]"),
            (43, "High [4h ; 20h] > 1.5 * Open 16h DAY-1"),
            (44, "High [4h ; 20h] > 1.7 * Open 16h DAY-1"),
            (45, "High [4h ; 20h] > 2 * Open 16h DAY-1"),
            (46, "High [4h ; 20h] > 2.3 * Open 16h DAY-1"),
            (47, "Low [4h ; 20h] < 0.5 * Open 16h DAY-1"),
        ]
        
        for i, (cond_id, desc) in enumerate(condition_defs):
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(self.scrollable_frame, text=f"{cond_id}. {desc}", variable=var)
            chk.grid(row=i, column=0, sticky=tk.W)
            self.conditions[cond_id] = var
    
    def get_default_date(self):
        today = datetime.datetime.today()
        if today.time() > datetime.time(20, 0):
            return (today + BDay(1)).date()
        return today.date()
    
    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.tickers = [line.strip() for line in f if line.strip()]
                if len(self.tickers) > 50:
                    messagebox.showerror("Error", "Maximum 50 tickers allowed")
                    self.tickers = []
                else:
                    messagebox.showinfo("Success", f"Loaded {len(self.tickers)} tickers")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def fetch_data(self, ticker, day_minus1, day):
        # Replace with actual IBKR API calls if needed.
        start = pd.Timestamp(f"{day_minus1} 16:00:00")
        end = pd.Timestamp(f"{day} 20:00:00")
        date_range = pd.date_range(start=start, end=end, freq='h')
        
        np.random.seed(hash(ticker) % 1000)
        opens = np.random.uniform(100, 200, len(date_range))
        return pd.DataFrame({
            'Open': opens,
            'High': opens + np.random.uniform(0, 10, len(date_range)),
            'Low': opens - np.random.uniform(0, 10, len(date_range)),
            'Close': opens + np.random.uniform(-5, 5, len(date_range))
        }, index=date_range)
    
    def evaluate_conditions(self, data, open_16h_day_minus1):
        results = {}
        try:
            # Conditions 1-14: For hours where we check that Close >= Open
            for hour in range(5, 20):
                if hour in [5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19]:
                    row = data.between_time(f"{hour:02d}:00", f"{hour:02d}:00").iloc[0]
                    results[hour] = row['Close'] >= row['Open']
            
            # Conditions 15-19: For hours where we check that High != Low
            for hour in range(15, 20):
                row = data.between_time(f"{hour:02d}:00", f"{hour:02d}:00").iloc[0]
                # We assign condition IDs 16 to 20 (i.e. hour+1)
                results[hour + 1] = row['High'] != row['Low']
            
            # Condition 20: For 18:00, check Open equals Low
            row = data.between_time('18:00', '18:00').iloc[0]
            results[20] = row['Open'] == row['Low']
            
            # Condition 21: For 18:00, check Close is not equal to High
            results[21] = row['Close'] != row['High']
            
            # Condition 22: Compare max High in two different time ranges
            high1 = data.between_time('04:00', '20:00')['High'].max()
            high2 = data.between_time('10:00', '15:00')['High'].max()
            results[22] = high1 == high2
            
            # Condition 23: For 18:00, check Close < Open
            results[23] = row['Close'] < row['Open']
            
            # Condition 24: For 18:00, check Open != High
            results[24] = row['Open'] != row['High']
            
            # Condition 25: For 18:00, check Close equals Low
            results[25] = row['Close'] == row['Low']
            
            # Condition 26: For 18:00, check High equals Low
            results[26] = row['High'] == row['Low']
            
            # Condition 27: Compare max High between two ranges (10:00-20:00 vs 04:00-20:00)
            high3 = data.between_time('10:00', '20:00')['High'].max()
            results[27] = high1 == high3
            
            # Condition 28: For 10:00, check Close < Open
            row10 = data.between_time('10:00', '10:00').iloc[0]
            results[28] = row10['Close'] < row10['Open']
            
            # Condition 29: For 10:00 vs 09:00, check High comparison
            row9 = data.between_time('09:00', '09:00').iloc[0]
            results[29] = row10['High'] >= row9['High']
            
            # Condition 30: For 10:00 vs 09:00, check Low comparison
            results[30] = row10['Low'] >= row9['Low']
            
            # Condition 31: For 16:00 and 17:00, check if Low at 17:00 <= Low at 16:00
            row16 = data.between_time('16:00', '16:00').iloc[0]
            row17 = data.between_time('17:00', '17:00').iloc[0]
            results[31] = row17['Low'] <= row16['Low']
            
            # Condition 32: For 17:00, check Open equals Low
            results[32] = row17['Open'] == row17['Low']
            
            # Condition 33: For 18:00, check Open equals High
            results[33] = row['Open'] == row['High']
            
            # Condition 34: For 18:00, check Close != Low
            results[34] = row['Close'] != row['Low']
            
            # Conditions 35-38: For 19:00 compared with earlier rows
            row19 = data.between_time('19:00', '19:00').iloc[0]
            results[35] = row19['Close'] > row16['Low']
            results[36] = row19['Low'] > row16['Low']
            results[37] = row19['Low'] > row17['Low']
            results[38] = row19['Low'] > row['Low']
            
            # Conditions 39-40: For 16:00, check equality of Open with Low and High
            row16 = data.between_time('16:00', '16:00').iloc[0]
            results[39] = row16['Open'] == row16['Low']
            results[40] = row16['Open'] == row16['High']
            
            # Conditions 41-42: Based on overall high in [04:00, 20:00]
            high_range = data.between_time('04:00', '20:00')['High'].max()
            results[41] = (row['Close'] < row['Open']) and (high_range is not None)
            results[42] = (row['Close'] >= row['Open']) and (high_range is not None)
            
            # Conditions 43-46: Compare overall high in [04:00,20:00] with multiples of Open 16h DAY-1
            results[43] = high1 > 1.5 * open_16h_day_minus1
            results[44] = high1 > 1.7 * open_16h_day_minus1
            results[45] = high1 > 2 * open_16h_day_minus1
            results[46] = high1 > 2.3 * open_16h_day_minus1
            
            # Condition 47: Compare min Low in [04:00,20:00] with 0.5 * Open 16h DAY-1
            low_range = data.between_time('04:00', '20:00')['Low'].min()
            results[47] = low_range < 0.5 * open_16h_day_minus1
            
        except IndexError:
            return False
        
        # Only the enabled conditions (via checkboxes) must be True.
        return all(results.get(cond_id, False) 
                   for cond_id, var in self.conditions.items() if var.get())
    
    def save_results(self):
        with open('screener_results.txt', 'w') as f:
            f.write("Num\tTicker\tOpen16hDay-1\n")
            for res in sorted(self.results, key=lambda x: x[0]):
                f.write(f"{res[0]}\t{res[1]}\t{res[2]:.2f}\n")
    
    def run_screener(self):
        # Clear previous results from the treeview.
        self.tree.delete(*self.tree.get_children())
        
        # Get screening date from the entry
        try:
            screening_date = datetime.datetime.strptime(self.date_entry.get(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format (YYYY-MM-DD)")
            return
        
        # Load OHLC data for each ticker using the screening date and previous day.
        day_minus1 = screening_date - datetime.timedelta(days=1)
        self.ohlc_data = {}
        for ticker in self.tickers:
            self.ohlc_data[ticker] = self.fetch_data(ticker, day_minus1, screening_date)
        
        # Evaluate conditions for each ticker.
        self.results = []
        for idx, ticker in enumerate(self.tickers):
            data = self.ohlc_data[ticker]
            # Assume the first row corresponds to the 16:00 bar on the previous day.
            open_16h = data.iloc[0]['Open'] if not data.empty else 0
            if self.evaluate_conditions(data, open_16h):
                self.results.append((idx+1, ticker, open_16h))
        
        # Display results in the treeview.
        for res in sorted(self.results, key=lambda x: x[0]):
            self.tree.insert("", "end", values=res)
        
        # Save results to file.
        self.save_results()
        messagebox.showinfo("Success", f"Found {len(self.results)} matches\nResults saved to screener_results.txt")
    
    def reset(self):
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, self.get_default_date().strftime("%Y-%m-%d"))
        self.tickers = []
        self.ohlc_data = {}
        self.results = []
        self.tree.delete(*self.tree.get_children())
        for var in self.conditions.values():
            var.set(True)

if __name__ == "__main__":
    root = tk.Tk()
    app = StockScreenerApp(root)
    root.mainloop()
