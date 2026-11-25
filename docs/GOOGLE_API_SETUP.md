# Google API setup

The recommended authentication path is GitHub OIDC plus Google Workload Identity Federation (WIF). Do not create or commit a service-account key.

1. Enable Google Drive API and Google Sheets API in a Google Cloud project.
2. Create a Workload Identity Pool/provider restricted to this GitHub repository and branch/environment.
3. Create a narrowly scoped service account and grant the external principal `roles/iam.workloadIdentityUser`.
4. Share only the target Drive folder and spreadsheet with that service account as editor.
5. Add `GOOGLE_WORKLOAD_IDENTITY_PROVIDER` and `GOOGLE_SERVICE_ACCOUNT` as production environment secrets.
6. Add `GOOGLE_DRIVE_FOLDER_ID`, optional `GOOGLE_SHEETS_ID`, and `GOOGLE_PUBLISH_ENABLED=true` as repository/environment variables.

The connected Drive target for this project is `台灣股市追蹤儀表板/02_市場資料/raw_csv` (`1_Heg7wdNdWgJ8HXgubeNaZUsVoXSMweW`). Use a different variable value when deploying from another account.

The application requests `drive.file` and `spreadsheets` scopes. Drive upload and Sheets append are isolated so a cloud failure is retained as an auditable `PARTIAL_SUCCESS` local result.

