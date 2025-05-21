import asyncio
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai

# Read Gemini API Key from file
with open("/home/minnu/Desktop/week 3/may 21/env3.txt") as f:
    api_key = f.read().strip()
genai.configure(api_key=api_key)

# ========== TOOL: PandasTool ==========
class PandasTool:
    def __init__(self):
        self.df = None

    async def load_csv(self, path):
        self.df = pd.read_csv(path)
        return self.df.head().to_string()

    async def describe_data(self):
        if self.df is not None:
            return self.df.describe().to_string()
        return "DataFrame is empty."

    async def clean_data(self):
        if self.df is not None:
            self.df.dropna(inplace=True)
            return "Missing values dropped."
        return "DataFrame is empty."

# ========== TOOL: MatplotlibTool ==========
class MatplotlibTool:
    async def plot_histogram(self, df, column):
        df[column].hist()
        plt.title(f"Histogram of {column}")
        filename = f"{column}_histogram.png"
        plt.savefig(filename)
        plt.close()
        return f"Histogram saved as {filename}"

# ========== AGENTS ==========
class DataFetcherAgent:
    def __init__(self, tools, csv_path):
        self.tools = tools
        self.csv_path = csv_path

    async def run(self):
        print("[DataFetcherAgent]: Fetching data...")
        output = await self.tools['pandas'].load_csv(self.csv_path)
        print(output)
        clean_status = await self.tools['pandas'].clean_data()
        print(clean_status)

class AnalystAgent:
    def __init__(self, tools):
        self.tools = tools

    async def run(self):
        print("[AnalystAgent]: Analyzing data...")
        summary = await self.tools['pandas'].describe_data()
        print(summary)
        # Plot histogram of first numeric column
        first_numeric_col = self.tools['pandas'].df.select_dtypes(include='number').columns[0]
        hist_status = await self.tools['matplotlib'].plot_histogram(self.tools['pandas'].df, first_numeric_col)
        print(hist_status)

# ========== RoundRobinGroupChat ==========
class RoundRobinGroupChat:
    def __init__(self, agents):
        self.agents = agents
        self.current_index = 0

    async def run_round(self):
        agent = self.agents[self.current_index]
        await agent.run()
        self.current_index = (self.current_index + 1) % len(self.agents)

# ========== MAIN PIPELINE ==========
async def main():
    csv_path = "/home/minnu/Desktop/week 3/may 21/Iris_missingdata.csv"

    # Instantiate tools
    pandas_tool = PandasTool()
    matplotlib_tool = MatplotlibTool()

    # Instantiate agents with tools
    data_fetcher = DataFetcherAgent(tools={"pandas": pandas_tool}, csv_path=csv_path)
    analyst = AnalystAgent(tools={"pandas": pandas_tool, "matplotlib": matplotlib_tool})

    # RoundRobinGroupChat with two agents
    group_chat = RoundRobinGroupChat([data_fetcher, analyst])

    # Run two rounds (one full cycle)
    for _ in range(2):
        await group_chat.run_round()

if __name__ == "__main__":
    asyncio.run(main())
