# How to run Socrates beta

This guide starts the local browser-based tutor on Windows with PowerShell. It covers the existing project workspace and a team member's first setup. The beta is intended for supervised local testing; it is not a public deployment.

## Before you start

You need Python 3.12, Git, the project code, and access to a compatible local textbook index. A live language model also needs an individual provider key and an internet connection. The source data and keys are deliberately excluded from Git.

The current local beta index is `ncert-2026-11-03-beta3` (10,878 passages/references). Its presence in the dataset report does not mean it is included in a fresh clone. More detail: [dataset report](datasets/DATASET_REPORT.md).

## A. Run on the existing project computer

Open PowerShell and run:

```powershell
Set-Location -LiteralPath 'D:\Work\IITB\Socratic Tutor'
.\socrates.ps1 datasets
```

The dataset listing should show an active dataset such as `ncert-2026-11-03-beta3`. If it reports missing data or an integrity error, use the troubleshooting section; do not delete or overwrite the existing dataset.

Start the full conversational tutor:

```powershell
.\socrates.ps1 serve --live
```

Open [http://127.0.0.1:8770](http://127.0.0.1:8770), choose a class, subject and topic, and ask a question. Keep PowerShell open while using the app. Press **Ctrl+C** in that window to stop it.

The existing computer's `config/beta/local.json` points to the separate team application checkout for its maths and language adapters. The launcher's selected Python environment and the provider key are read from that configured application setup. Do not replace the existing configuration or environment just to follow the fresh-setup steps below.

### Offline source-reading mode

To start without a provider key or model call, omit `--live`:

```powershell
.\socrates.ps1 serve
```

This uses a labelled, source-backed fallback; it does not reproduce the live model's natural-language conversation. Existing checked maths practice can still be used.

## B. First-time setup for a team member

1. Install Git and Python 3.12, and get access to the repository. In PowerShell, check `git --version` and `py -3.12 --version`.
2. Clone the branch containing this guide into a new folder. The `milestone-2` branch is currently local and must be published before another machine can clone it. Once published, run this from the parent folder where you want the new checkout:

   ```powershell
   git clone --branch milestone-2 https://github.com/ksharp05/Socratic-AI-Tutor.git
   Set-Location -LiteralPath '.\Socratic-AI-Tutor'
   ```

   If you already have a checkout, fetch and switch to `milestone-2` instead; do not clone over your existing files.
3. Create a project environment and install the application and beta dependencies:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -e '.[dev,api]' -r requirements-beta.txt
   ```

4. **Obtain compatible local data.** The Git clone does not include `Directions/`, the source PDFs, the extracted indexes or private evaluation data. Obtain an appropriately authorized, compatible prepared index and its independently supplied SHA-256 from the data owner; consult the [source catalogue](datasets/NCERT_CATALOGUE.md) and publisher terms before transferring data. Do not copy an existing `registry.json`: it contains absolute paths. With an authorized prepared index stored at a stable local path, register it in the new checkout:

   ```powershell
   .\socrates.ps1 register-index --file 'C:\path\to\authorized\knowledge.sqlite' `
     --id 'local-ncert-beta' --title 'Local NCERT beta' --activate `
     --expected-sha256 '<trusted-lowercase-sha256>'
   .\socrates.ps1 datasets
   ```

   Replace the placeholders. Get the trusted expected hash separately from the index file; calculating a hash from an untrusted file and comparing it to itself does not verify provenance. Registration checks the hash, schema, search index and pending-review labels, then records the index's path; keep that file at that path. Do not copy source data into Git. A relocated copy of the current beta index was tested in an isolated workspace **on the original computer**, including health and retrieval checks in the three maths chapters. A second-machine, fresh-clone and Docker acceptance is still outstanding.
5. Configure the data location (set this before the registration command if the data workspace is separate from the checkout). `config/beta/local.example.json` is used automatically when `config/beta/local.json` is absent. Its defaults use this checkout as the application root and `Directions/beta_data` relative to the source workspace. If the data lives in another folder, set that folder for the current PowerShell session:

   ```powershell
   $env:SOCRATES_SOURCE_WORKSPACE = 'C:\path\to\workspace-containing-Directions'
   ```

   Replace the example path. If you need different settings, copy `config/beta/local.example.json` to `config/beta/local.json` and edit it. `app_root` points to the application checkout; `data_directory` points to the beta data folder, either absolutely or relative to the source workspace. The local config is Git-ignored.
6. For live conversation, create your own `.env` in the application root from `.env.example` **only if `.env` does not already exist**. Put your personal key after `LLM_API_KEY=` and save the file. The default provider and model are in `config/app.toml`; environment variables can override them. Never commit or share your key. An existing shell environment variable takes precedence over the `.env` entry. Use `TUTOR_LLM=stub` only when deliberately disabling the live model.

   ```powershell
   if (-not (Test-Path -LiteralPath '.env')) {
       Copy-Item -LiteralPath '.env.example' -Destination '.env'
   }
   notepad .env
   ```

7. Once the data setup is available, check it with `.\socrates.ps1 datasets`, then run `.\socrates.ps1 serve --live`. For offline source reading, run `.\socrates.ps1 serve` instead. Open `http://127.0.0.1:8770`.

The PowerShell launcher picks `SOCRATES_PYTHON` first, then `.venv_beta`, then `.venv` under the configured application root. If you set `SOCRATES_PYTHON`, it must point to an environment with the required dependencies.

## Check that it is running

1. Open [http://127.0.0.1:8770/api/health](http://127.0.0.1:8770/api/health). A healthy local setup reports `status: ok`, the dataset and language mode. The dataset integrity status should be `verified`.
2. Open the main page, choose an available subject and ask a concept question in English. Check the cited source and the displayed provider/fallback status.
3. For checked practice, choose Class 10 Maths and one of Quadratic Equations, Arithmetic Progressions or Introduction to Trigonometry. These are the current supported maths-practice chapters; other subjects are source-grounded concept conversation, not equivalent checked practice.
4. Try the documented examples in [questions to try](beta/QUESTIONS_TO_TRY.md). The development results and graph are not an independent evaluation or proof of teaching quality.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `No configured language provider` | Check the key in the application root's ignored `.env` or the current environment; check that `TUTOR_LLM` is not `stub`. Restart the server. Use offline mode if a key is unavailable. |
| Provider errors or fallback during live use | Check connectivity, key/model access and provider credit. Live calls can incur charges; the default budget is 60 calls per server run, with a maximum of 120. Fallback can also follow output-validation failure or budget exhaustion. |
| Missing `BUILD_REPORT.json`, index, source file or hash mismatch | Confirm that `SOCRATES_SOURCE_WORKSPACE` points to the workspace containing `Directions/`, and that a compatible, intact data setup is available. A fresh clone alone is insufficient. Do not bypass hash checks. |
| No Python or missing package | Ensure Python 3.12 and the project dependencies are installed. Check launcher environment selection and `SOCRATES_PYTHON`. |
| Port 8770 is in use | A tutor may already be running; open the URL first. Otherwise start a second instance with `.\socrates.ps1 serve --port 8771` (add `--live` for live mode) and open `http://127.0.0.1:8771`. |
| `socrates.ps1` is blocked by PowerShell | Check your organization's script-execution policy. Do not change machine-wide security settings; use an approved local configuration or ask your administrator. |
| No result for a topic | Select the correct grade, subject and available book. The dataset includes fewer indexed passages than source books; some maths notation and non-English content are not supported. |

## Further information

- [Beta features, dataset import and evaluation](beta/README.md)
- [Dataset report](datasets/DATASET_REPORT.md) and [book catalogue](datasets/NCERT_CATALOGUE.md)
- [Team setup guide](https://github.com/ksharp05/Socratic-AI-Tutor/blob/milestone-1/Docs/SETUP.md), which describes the separate original proof of concept as well as general Git and Python setup.
