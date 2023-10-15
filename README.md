<div align="center">

[![Python 3.11+](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![unit-tests](https://github.com/Bilbottom/daily-tracker/actions/workflows/unit-tests.yaml/badge.svg)](https://github.com/Bilbottom/daily-tracker/actions/workflows/unit-tests.yaml)
[![coverage](coverage.svg)](https://github.com/dbrgn/coverage-badge)
[![GitHub last commit](https://img.shields.io/github/last-commit/Bilbottom/daily-tracker)](https://shields.io/)

[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Bilbottom/daily-tracker/main.svg)](https://results.pre-commit.ci/latest/github/Bilbottom/daily-tracker/main)
[![Sourcery](https://img.shields.io/badge/Sourcery-enabled-brightgreen)](https://sourcery.ai)

</div>

---

# Daily Tracker ⏱️📝

An application for keeping track of tasks throughout the day.

Not sure where all your time goes? I wasn't either 😄 This application generates a pop-up box every 15 minutes (configurable) to fill out what you're currently working on.

> This is a work in progress. I'm currently using it to track my time, but it's not yet ready for public consumption.

## ✨ Features

The GUI is currently built with [Tkinter](https://docs.python.org/3/library/tkinter.html) and looks like:

<div align="center">
    <img src="tracker-form-tkinter.png" width=350 alt="tkinter-form" />
</div>

This pop-up box has the following features:

- Drop-down box to select from recent projects
- Drop-down box to select the selected project's recent details
- By default, autopopulates the project and details from the previous entry
- Has a Streamlit front-end for viewing and editing the data
- Integrates with [Outlook <img alt="Microsoft Outlook" height="14px" src="https://outlook.live.com/favicon.ico"/>](https://outlook.live.com/owa/) (macOS and Windows)
  - Reads the calendar and autofills with meeting information
- Integrates with [Jira <img alt="Jira Software" height="12px" src="https://example.atlassian.net/favicon.ico">](https://www.atlassian.com/software/jira)
  - Reads tickets in the current sprint and adds them to the project drop-down
  - Adds a worklog to the ticket when the form is submitted
- Integrates with [Slack <img alt="Slack" height="12px" src="https://slack.com/favicon.ico"/>](https://slack.com/)
  - Posts a message to channel when the form is submitted

## 🔧 Resources and dependencies

The clock icon is from [icons8.com](https://icons8.com/):

- https://icons8.com/icon/2YPST59G2xJZ/clock

### 🍎 On macOS

On macOS, you will probably need to install the Tcl/Tk framework:

```bash
brew install tcl-tk
```

This has been tested and confirmed to work on an M1 Mac with version `8.6.13` of the `tcl-tk` package, running Python `3.11.4` (installed using [pyenv](https://github.com/pyenv/pyenv)).

More details available at:

- https://tkdocs.com/tutorial/install.html#install-macos
