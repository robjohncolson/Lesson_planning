# Installing the Teacher Console

The Teacher Console is a lesson-management tool that runs entirely on your laptop — no account, no internet connection required once set up. It gives you a browser-based interface where you can view and edit lesson YAML files and regenerate student and teacher PDF packets.

This guide is for Windows 10 or Windows 11 users who have not used Git, Python, or a terminal before. Follow every step in order.

**What you need before starting:**
- A Windows 10 or 11 laptop
- About 30 minutes
- Roughly 5 GB of free disk space (MiKTeX, the PDF engine, is the large piece)

---

## Step 1 — Install Git for Windows

Git gives you the Git Bash terminal, which is how you will run commands in this guide.

1. Go to **https://git-scm.com/download/win** and download the installer.
2. Run the installer. Click **Next** through every screen — the default options are fine.
3. When the installer finishes, search your Start menu for **Git Bash** and open it. You should see a dark terminal window with a `$` prompt.

![Git Bash open and ready](docs/install_screenshots/1_git_bash.png)

> If you do not see Git Bash in the Start menu, restart your computer and try again.

---

## Step 2 — Install Python 3.11 or newer

1. Go to **https://www.python.org/downloads/windows/** and click the yellow **Download Python 3.x.x** button.
2. Run the installer.
3. **CRITICAL:** On the very first screen of the installer, check the box that says **"Add Python to PATH"** before clicking Install Now.

![Python installer — check Add Python to PATH](docs/install_screenshots/2_python_path_checkbox.png)

4. Click **Install Now** and let it finish.

**Verify it worked.** Open Git Bash and type:

```bash
python --version
```

You should see something like `Python 3.11.9`. If you see `command not found` or a Microsoft Store pop-up, Python was not added to PATH — uninstall Python and repeat step 2, making sure to check the box.

---

## Step 3 — Install MiKTeX

MiKTeX is the engine that compiles LaTeX files into the PDFs you print and hand to students.

1. Go to **https://miktex.org/download** and click the **Download** button under the Windows section.
2. Run the installer.
3. When asked **"Install MiKTeX for:"**, choose **"Only for me (recommended)"**.
4. When asked about installing missing packages on the fly, choose **"Yes"** (or "Always install missing packages on-the-fly"). This lets MiKTeX automatically download any LaTeX package it needs the first time you compile a document.
5. Click through the remaining screens with the default settings.

![MiKTeX install — choose Yes for on-the-fly packages](docs/install_screenshots/3_miktex_on_the_fly.png)

---

## Step 4 — Clone the repository

"Cloning" downloads a copy of all the lesson files to your laptop.

Open **Git Bash** and run these two commands one at a time (press Enter after each):

```bash
cd ~/Documents
git clone https://github.com/robjohncolson/Lesson_planning.git
```

This creates a folder called `Lesson_planning` inside your Documents. Navigate into it:

```bash
cd Lesson_planning
```

Your Git Bash prompt will now show you are inside the `Lesson_planning` folder.

---

## Step 5 — Install Python packages

The console needs three small Python libraries. Install them with one command:

```bash
python -m pip install flask pyyaml ftfy
```

You will see a stream of download messages. Wait for it to finish — it usually takes under a minute.

---

## Step 6 — Launch the Teacher Console

Still in Git Bash (inside the `Lesson_planning` folder), run:

```bash
python console.py
```

You should see:

```
Teacher Console running at http://127.0.0.1:5173
Press Ctrl+C to stop.
```

Your default browser will open automatically to the console. If it does not open on its own, type **http://127.0.0.1:5173** into your browser's address bar.

![Teacher Console home — lesson grid on left](docs/install_screenshots/6_console_home.png)

> To stop the console later, click back into Git Bash and press **Ctrl + C**.

---

## Step 7 — First use

- The **lesson grid** on the left lists every available lesson (e.g. L41\_P1, L41\_P2).
- Click any lesson to open it.
- The **YAML editor** on the right lets you read or edit the lesson spec.
- The **PDF preview** shows the current student or teacher packet.
- The **Regenerate** button rebuilds the PDF from the YAML. The first regeneration may take an extra minute while MiKTeX downloads needed packages — let it run.

---

## Troubleshooting

**"python is not recognized as an internal or external command"**
You did not check the **Add Python to PATH** box during installation. Uninstall Python from *Settings → Apps*, then repeat Step 2 and check that box.

---

**"pdflatex command not found" or regeneration always fails with a compile error**
MiKTeX was not added to your system PATH. Uninstall MiKTeX from *Settings → Apps*, then repeat Step 3. During reinstall, accept any prompt that offers to add MiKTeX to PATH. After reinstalling, close Git Bash completely, reopen it, and try again.

---

**"Port 5173 is already in use"**
Another program is using that port. Run the console on a different port:

```bash
python console.py --port 5174
```

Then open **http://127.0.0.1:5174** in your browser.

---

**MiKTeX opens a pop-up asking to install package X**
Click **Install**. MiKTeX will download and install the package automatically. The PDF will finish compiling after the download. This only happens once per missing package.

---

**The Regenerate button does nothing, or spins forever**
Switch back to the Git Bash window where `console.py` is running — the error will be printed there. The most common cause is a LaTeX compile error or a missing package that could not be installed silently. Copy the red error lines and email them for help.

---

## Uninstalling

1. Delete the `Lesson_planning` folder from your Documents.
2. To remove the software: go to *Settings → Apps* and uninstall **Python**, **MiKTeX**, and **Git** in any order.

---

## Getting help

If you get stuck, email **lynnlegorobot@gmail.com** or open an issue at **https://github.com/robjohncolson/Lesson_planning/issues**.
