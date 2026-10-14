# Steam Signals: game engagement dashboard

An interactive dashboard exploring how game genre, release year, and price relate to player activity and review sentiment on Steam.

## Questions

1. Which genres have the largest recorded peak player audiences?
2. How do price and genre relate to review sentiment and player activity?

The dashboard treats peak concurrent players and player reviews as **engagement signals**, not sales figures.

## Run it on your computer

1. Install [Python](https://www.python.org/downloads/) if you don't already have it.
2. Download or clone this folder.
3. Open a terminal in this folder and install the app packages:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the dashboard:

   ```bash
   python -m streamlit run app.py
   ```

Streamlit will open the dashboard in your browser. The CSV is included, so the app does not need to fetch data at startup.

## Publish a shareable URL with GitHub and Streamlit Community Cloud

### Put the project on GitHub

1. Sign in to [GitHub](https://github.com/) and create a new repository, for example `steam-game-engagement-dashboard`.
2. Set it to **Public** if you want anyone to be able to inspect the project files. Do not add a README or other starter files; this folder already contains them.
3. Choose **Add file → Upload files** and upload the contents of this folder: `app.py`, `requirements.txt`, `README.md`, `.gitignore`, and the `data` folder.
4. Commit the uploaded files to the repository's `main` branch.

### Deploy it

1. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub and grant it access to the repository.
2. Choose **Create app** and select the repository, `main` branch, and `app.py` as the main file.
3. Choose **Deploy**. Streamlit installs the packages listed in `requirements.txt` and builds the app.
4. When deployment finishes, copy the `*.streamlit.app` link and open it in a private/incognito browser window to confirm that other people can view it.

The app and its data stay in the GitHub repository. To update the live dashboard later, upload or commit the changed files to `main`; Community Cloud redeploys from the connected repository.

## Data and interpretation

- **Dataset:** [Fronkon Games Steam Games Dataset](https://huggingface.co/datasets/FronkonGames/steam-games-dataset), built from the Steam API and Steam Spy. The dataset card describes 124,146 game records and lists an MIT license.
- **Snapshot:** this project retrieved the dataset on October 14, 2026 and saved only the fields needed for the dashboard in `data/steam_games.csv`.
- **What the fields mean:** peak concurrent users is a recorded player peak; review counts are community feedback. Neither tells us the number of copies sold or revenue.
- **Review sentiment:** positive reviews divided by all positive and negative reviews. A sidebar control sets the minimum review count used in review comparisons.
- **Genre:** games can have several Steam genres. For the genre comparisons, this dashboard uses the first genre listed in the dataset.
- **Price:** the included USD price is a snapshot and may vary by region or sale.

## Files

- `app.py` — Streamlit dashboard
- `data/steam_games.csv` — compact data extract used by the dashboard
- `requirements.txt` — packages installed locally or by Streamlit Cloud
