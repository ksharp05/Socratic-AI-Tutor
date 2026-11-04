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

## Connected graph tutor: local offline demo

> **Development content:** Quizzes use separate synthetic development packs: six quadratic questions and six AP/trigonometry questions. Teacher approval is required in the mounted tutor; human content review and independent evaluation remain pending. See [mode and provenance details](m2/KEY_AND_MODE_INTEGRITY.md).


The standalone beta launch above does not mount the authenticated graph. To try the connected graph tutor on this computer, use a separate PowerShell window and a local beta configuration whose registered dataset is already available. This example uses an isolated graph data directory, obvious development-only credentials, and stub models; do not expose it on a public network.

```powershell
Set-Location -LiteralPath 'D:\Work\IITB\Socratic Tutor'
$env:SOCRATES_SOURCE_WORKSPACE = (Get-Location).Path
$env:TUTOR_BETA_WORKSPACE = (Get-Location).Path
$env:TUTOR_BETA_CONFIG = Join-Path (Get-Location) 'config\beta\local.json'
$env:TUTOR_VAR_DIR = Join-Path (Get-Location) 'Directions\connected_demo_state'
$env:TUTOR_LLM = 'stub'
$env:TUTOR_BETA_LIVE = '0'
$env:TUTOR_API_SEED = '1'
$env:TUTOR_API_TOKENS = 'local-student:student:L-DEMO,local-teacher:teacher:T-DEMO'
$env:PYTHONPATH = (Join-Path (Get-Location) 'src') + ';' + (Join-Path (Get-Location) 'socratic_tutor_dataset_v2\src')
.\.venv_app\Scripts\python.exe -m uvicorn tutor_api.main:app --host 127.0.0.1 --port 8771
```

Keep the server window open. In another PowerShell window, make a **synthetic development approval** so the local demo has questions:

```powershell
$teacherHeaders = @{ Authorization = 'Bearer local-teacher' }
$proposal = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8771/teacher/proposals' -Headers $teacherHeaders -ContentType 'application/json' -Body '{"concept_id":"qe04"}'
$null = Invoke-RestMethod -Method Post -Uri ("http://127.0.0.1:8771/teacher/proposals/" + $proposal.set_id + "/approve") -Headers $teacherHeaders
$quizProposal = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8771/teacher/proposals' -Headers $teacherHeaders -ContentType 'application/json' -Body '{"concept_id":"qe04","mode":"quiz"}'
$null = Invoke-RestMethod -Method Post -Uri ("http://127.0.0.1:8771/teacher/proposals/" + $quizProposal.set_id + "/approve") -Headers $teacherHeaders
```

To add synthetic development practice and quiz approvals for the other two chapters, run the following in the same second window. These automated local approvals are for demonstration only; they are not educator reviews.

```powershell
foreach ($concept in @('ap03', 'tr01')) {
    foreach ($mode in @('practice', 'quiz')) {
        $body = @{ concept_id = $concept; mode = $mode } | ConvertTo-Json -Compress
        $draft = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8771/teacher/proposals' -Headers $teacherHeaders -ContentType 'application/json' -Body $body
        $null = Invoke-RestMethod -Method Post -Uri ("http://127.0.0.1:8771/teacher/proposals/" + $draft.set_id + "/approve") -Headers $teacherHeaders
    }
}
```

Open [the connected tutor](http://127.0.0.1:8771/beta/#connected) and enter `local-student`. Choose quadratic equations, arithmetic progressions, or trigonometry and ask a question. Start a new conversation to change the chapter. Normalized references display their textbook anchors and pending review status. Checked practice is available in all three chapters after separate teacher publication. The development quiz is available in each chapter after separate quiz-mode publication; completing an AP/trigonometry quiz creates that chapter’s graph plan. For AP or trigonometry, a teacher can create and review a proposal using concept `ap03` or `tr01` in the teacher interface, selecting `practice` or `quiz`; approval publishes that exact selected payload. [Chapter quizzes and plans](m2/CHAPTER_QUIZZES_AND_PLANS.md). See [chapter practice](m2/CHAPTER_PRACTICE.md). The two approvals above cover quadratics only and are separate because practice and quiz items have different permitted modes; AP/trigonometry need separate approvals. Signing out does not delete its data; the anonymous beta profile is a separate record. Press **Ctrl+C** in the server window to stop the server. The isolated graph database remains in `Directions\connected_demo_state`; the beta configuration selects its own dataset and beta storage.

The local browser walkthrough was verified with a synthetic index and the stub model; this exact command against your existing dataset has not been verified as a fresh-machine setup. Questions approved by the example are for development and do not constitute educator review. See [connected journey and limitations](m2/CONNECTED_GRAPH_JOURNEY.md).


## Integrated Compose preparation

The following is an **unverified Docker path**: Docker was unavailable on the development computer, so a clean-machine build and Compose health check remain required. It uses the integrated `/beta` mount and an authorised prepared index. Obtain the expected SHA-256 separately from a trusted source; do not rely only on a hash computed from an untrusted input. In PowerShell from the checkout containing the Docker files:

```powershell
$env:TUTOR_INDEX_PATH = 'C:\path\to\authorized\knowledge.sqlite'
$env:TUTOR_INDEX_SHA256 = '<trusted-lowercase-sha256>'
$env:TUTOR_DATASET_ID = 'local-prepared-index'
$env:TUTOR_API_TOKENS = 'local-student:student:L-DEMO,local-teacher:teacher:T-DEMO'
docker compose -f docker-compose.yml -f docker-compose.integrated.yml up --build --wait
Invoke-RestMethod http://127.0.0.1:8000/health/ready
```

Replace the placeholders. The example tokens are for isolated local development; use separately provisioned credentials for a real deployment. Open `http://127.0.0.1:8000/beta/#connected` for the connected browser or `http://127.0.0.1:8501` for the Streamlit teacher interface. Publish separate practice and quiz proposals for each chapter as described above. The existing Compose ports bind on the host interfaces, so use this development configuration only on a trusted local network.

To stop the stack without deleting its persistent volume, run `docker compose -f docker-compose.yml -f docker-compose.integrated.yml down`. Keep the same index path, ID and hash for restarts; the startup refuses to replace a different active dataset. The index is mounted read-only and is not copied into the image. The overlay forces offline stub mode. [Details and limitations](m2/INTEGRATED_COMPOSE.md).


In connected trigonometry practice, an ambiguous ratio answer may prompt a request for the reference angle and side lengths. Reply with the labels from your question, for example “angle C, opposite ..., adjacent ..., hypotenuse ...”. The tutor checks those labels and then asks you to choose the ratio; the final numeric answer is graded separately. [Supported forms and limits](m2/TRIANGLE_REASONING.md).

## Delete a connected learner record

Use the teacher interface's **Data requests** page with a synthetic learner when demonstrating deletion. The teacher must confirm the learner ID and authority for the request; deletion returns a receipt and cannot be undone. It removes that signed-in graph record, owned registered checkpoints and traces, and blocks reuse by the old credential. The anonymous beta browser history is separate. A pending/busy deletion must be retried by the teacher; do not reset the database to clear it. [Workflow and recovery](m2/LEARNER_DATA_LIFECYCLE.md) and [memory policy](MEMORY_POLICY.md) describe retained deletion metadata, backup/physical-erasure limitations and the separate browser-clear action.
