# Fresh Python installation and Windows container prerequisites

Verified 4 November 2026, from clean local clone `14f55b6cb7c0dbeff73b4ab5c95ba61ddfe7aba1` on `milestone-2`.

## Installed and checked

| Component | Observation |
|---|---|
| Docker Desktop | 4.98.0, official signed installer, matching published SHA-256, installation exit 0 |
| Docker CLI / Compose | 29.9.2 / 5.6.1; base `docker compose -f docker-compose.yml config --quiet` passed |
| WSL | 2.7.14.0, official signed Microsoft MSI, matching release SHA-256, installation exit 0 |
| Virtual Machine Platform | Enabled with no automatic restart; Windows reports restart required |
| Python | 3.12.10; fresh standard virtual environment with system site packages disabled |
| Dependencies | Editable `[dev,api,ui]` installation plus `requirements-beta-dev.txt` succeeded from PyPI; 134 install-report records, 136 installed distributions including bootstrap tooling |
| Dependency consistency | `pip check` passed in fresh environment and existing application environment; pip restored with `ensurepip` in the latter |

The fresh clone contained no copied `.env` or private source data. Imports for `tutor`, `socratic_data`, `ncert_pipeline` and `socrates_beta` resolved inside that clone. The local install report and freeze are retained as evidence, not presented as a portable dependency lock.

## Actual test outcomes

The first four-suite run without private local fixtures had **390 passes and 34 setup errors**: the prepared textbook pipeline report/data and expanded-v0.2 source snapshot were absent. Installing additional Python packages does not supply these files.

The same fresh environment and checkout then ran all four suites with `SOCRATES_SOURCE_WORKSPACE` explicitly pointing to the existing authorised local dataset and `SOCRATES_TEAM_APP_ROOT` pointing to the fresh clone: **424 passed in 91.78 seconds**. `TUTOR_LLM=stub`, `TUTOR_BETA_LIVE=0` and disabled tracing kept this run offline. No provider calls were made. This establishes clean dependency installation with supplied data on the same Windows machine; it does not establish a data-independent checkout, second-machine portability or container acceptance.

Local ignored evidence: `Directions/git_delivery/m2_clean_install_current.json`, the referenced run's install report, environment provenance and both test logs/JUnit files, and `Directions/git_delivery/system-dependencies/verification.json`. Successful test log SHA-256: `66fe7a60ed20e699805f641048efee0e18baacb068b1a15c5930d4ef6a14196c`.

## Resume after restart

1. Restart Windows when ready, then open Docker Desktop and allow its WSL backend to initialise. No automatic restart was performed.
2. In a new terminal run `wsl --version`, `docker version` and `docker compose version`. `docker version` must show a responding server as well as the client.
3. Verify Docker's actual storage location. The installer requested `D:\DockerData\wsl`; first-start settings/VHD placement have not yet been observed.
4. Follow [integrated Compose preparation](INTEGRATED_COMPOSE.md) and the [run guide](../RUN_GUIDE.md), supplying the authorised index and separately trusted expected hash. Verify image build, service readiness, authenticated UI and restart/persistent-volume behavior with retained logs.

Docker Desktop was stopped at verification. Engine startup, image builds, container health, integrated overlay execution and volume recovery remain unverified until after the restart. These installation results do not change content-review or live-model acceptance gates.
