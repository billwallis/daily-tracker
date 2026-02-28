<span align="center">

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![tests](https://github.com/billwallis/daily-tracker/actions/workflows/tests.yaml/badge.svg)](https://github.com/billwallis/daily-tracker/actions/workflows/tests.yaml)
[![coverage](https://raw.githubusercontent.com/billwallis/daily-tracker/refs/heads/main/coverage.svg)](https://smarie.github.io/python-genbadge/)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/billwallis/daily-tracker/main.svg)](https://results.pre-commit.ci/latest/github/billwallis/daily-tracker/main)
[![GitHub last commit](https://img.shields.io/github/last-commit/billwallis/daily-tracker)](https://shields.io/)

</span>

---

# Daily Tracker ⏱️📝

An application for keeping track of tasks throughout the day.

Not sure where all your time goes? I wasn't either 😄 This application generates a pop-up box every 15 minutes (configurable) to fill out what you're currently working on.

> [!WARNING]
>
> This is a work in progress. I'm currently using it to track my time, but it's not yet ready for public consumption.

## Features

The GUI is currently built with [Tkinter](https://docs.python.org/3/library/tkinter.html) and looks like:

<div align="center">
    <img src="tracker-form-tkinter.png" width=350 alt="tkinter-form" />
</div>

This pop-up box has the following features:

- Drop-down box to select from recent projects
- Drop-down box to select the selected project's recent details
- By default, autopopulates the project and details from the previous entry
- Integrates with:
  - [Google Calendar <img alt="Google Calendar" height="12px" src="https://calendar.google.com/googlecalendar/images/favicons_2020q4/calendar_28.ico"/>](https://calendar.google.com/)
  - [Outlook <img alt="Microsoft Outlook" height="14px" src="https://outlook.live.com/favicon.ico"/>](https://outlook.live.com/owa/)
  - [Jira <img alt="Jira Software" height="12px" src="https://example.atlassian.net/favicon.ico">](https://www.atlassian.com/software/jira)
  - [Slack <img alt="Slack" height="12px" src="https://slack.com/favicon.ico"/>](https://slack.com/)
  - [GitHub <img alt="GitHub" height="12px" src="https://github.com/favicon.ico"/>](https://github.com/)
  - [Monday.com <img alt="Monday.com" height="12px" src="https://monday.com/favicon.ico"/>](https://monday.com/)

## Resources and dependencies

The clock icon is from [icons8.com](https://icons8.com/):

- https://icons8.com/icon/2YPST59G2xJZ/clock

### macOS

On macOS, you will probably need to install [the Tcl/Tk framework](https://www.tcl-lang.org/):

```bash
brew install tcl-tk
```

More details available at:

- https://tkdocs.com/tutorial/install.html#install-macos

## Usage

Configure the [configuration.yaml](src/daily_tracker/resources/configuration.yaml) appropriately, and add any required [environment variables](.env.example). Check the available CLI commands with:

```shell
daily-tracker --help
```

## Contributing

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and then install the dependencies:

```bash
uvx --from poethepoet poe install
```
