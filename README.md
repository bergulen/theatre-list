# Theatre list

A personal list of upcoming performances for the plays I follow on tiyatrolar.com.tr. It checks the play pages every morning and shows every date, time and venue in one list.

## What's in this folder

| File | What it does |
|---|---|
| `plays.txt` | The plays you follow. One tiyatrolar.com.tr link per line. |
| `scrape.py` | Reads each play page and saves the performances to `data.json`. |
| `data.json` | The saved list of performances. Updated automatically. |
| `index.html` | The page you open to see the list. |
| `.github/workflows/update.yml` | Tells GitHub to run `scrape.py` every day at 07:00 Istanbul time. |
| `requirements.txt` | The two Python libraries the script needs. |

## One-time setup

**1. Create the repository.** On github.com, click **New repository**. Name it `theatre-list`, set it to **Public** (GitHub Pages is free for public repos), and create it without a README.

**2. Put the files in it with VS Code.**
1. In VS Code, open the Command Palette (Ctrl+Shift+P, or Cmd+Shift+P on Mac), run **Git: Clone**, and paste your new repo's URL. Choose a folder on your computer.
2. Copy everything from this folder into the cloned folder, including the hidden `.github` folder. On a Mac, press Cmd+Shift+. in Finder to see hidden folders.
3. Open the **Source Control** panel (the branch icon on the left), type a message like "First version", click **Commit**, then **Sync Changes**.

**3. Let the daily job save its results.** In the repo on github.com, go to **Settings → Actions → General → Workflow permissions**, choose **Read and write permissions**, and save.

**4. Turn on the web page.** Go to **Settings → Pages**. Under **Build and deployment**, set Source to **Deploy from a branch**, then choose branch **main** and folder **/ (root)**. Save. After a minute or two, your page will be at:

`https://YOUR-USERNAME.github.io/theatre-list/`

**5. Run the first check.** Go to the **Actions** tab, click **Update theatre list**, then **Run workflow**. When it shows a green check, reload your page.

**6. Put it on your Mac.**
- Safari (macOS Sonoma or later): open the page, then **File → Add to Dock**. It becomes its own app with its own window.
- Chrome: menu **⋮ → Cast, save and share → Create shortcut**, tick **Open as window**.

Resize the window small and keep it in a corner, the way you would with Stickies. (Menu names shift a little between versions.)

## Everyday use

**Follow a new play.** Click **Add or remove plays** at the top of the page. It opens `plays.txt` on GitHub. Paste the play's link on a new line and click **Commit changes**. The list refreshes within a few minutes.

**The notes.** Each play gets its own sticky note listing its upcoming dates, with the soonest play first.
- Next to each date: **★** interested, **✓** tickets bought, **–** hide the date. Press again to undo.
- Click a note's top strip to fold it down to just the title, and the small square in the corner to change its color.
- The tabs at the top show only starred or bought dates. **Show hidden** brings hidden dates back.

Marks, colors and folds are saved in your browser, so they won't appear on another computer.

**What you'll see.**
- Past performances drop off automatically.
- **New date** marks performances that appeared in the last 3 days.
- Plays with no upcoming dates still get a note saying so, so you know they're still being checked.

**Check right now.** Click **Check for new dates now**, then **Run workflow**.

## Testing locally in VS Code (optional)

In VS Code's terminal (Terminal → New Terminal):

```
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac: source .venv/bin/activate
pip install -r requirements.txt

# See what the script reads from a page, without changing anything:
python scrape.py --check https://tiyatrolar.com.tr/tiyatro/ehlikeyf

# Update data.json and preview the page:
python scrape.py
python -m http.server 8000
```

Then open http://localhost:8000 in your browser.

## If something stops working

- **A play shows an error at the bottom of the page.** The link may be wrong, or the site was down that morning. Yesterday's dates stay on the list until the next successful check.
- **A play has dates on the website but none on your list.** The site may have changed its page layout. Run `python scrape.py --check <link>` to see what the script reads. The date-reading code is in `parse_sessions` in `scrape.py`.
- **The daily update stopped.** GitHub pauses scheduled jobs in repos with no activity for 60 days, and emails you before it does. Go to the **Actions** tab and click **Enable workflow**.
