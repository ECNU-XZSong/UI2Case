# UI2Case RICO-36 Data

This directory contains the public RICO-36 data retained with the UI2Case method package.

## Composition

- 36 cases.
- 158 UI screens.
- 122 human-verified screen transitions.
- 737 reference interaction points.
- 12 application categories and 3 complexity levels.

## Per Case

```
cases/<case_id>/
  screenshots/Page_i.jpg
  meta.json
  groundtruth/navigation.json
  groundtruth/layout.json
  groundtruth/interaction.json    {Page_i: [clickable points]}
```
