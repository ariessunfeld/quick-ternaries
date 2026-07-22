# Local Bug-Report Data

Put reporter-provided workbooks and CSV files in a report-specific directory:

```text
local-test-data/
└── reporter-bug-summary/
    ├── original.xlsx
    └── notes.md
```

Everything below this directory except this README is ignored by Git. Keep the
original file unchanged while reproducing the report. After identifying the
smallest failing case, add a generated or minimized regression fixture under
`tests/data/`; automated tests must not depend on files in `local-test-data/`.

Suggested workflow:

1. Move the reporter's file into a clearly named subdirectory.
2. Record the reproduction steps and relevant columns in a local `notes.md`.
3. Reproduce the behavior through the application.
4. Add a failing automated test using generated data whenever possible.
5. Use a small workbook in `tests/data/` only when the workbook structure is
   itself necessary to reproduce the failure.
6. Implement the fix, run the focused test, then run the complete test suite.
7. Manually confirm the result with the original reporter file.
