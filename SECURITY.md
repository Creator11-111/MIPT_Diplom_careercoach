# Security and Privacy

## Secret Management

This project uses environment variables for all sensitive configuration. Never commit secrets to version control.

### Excluded from Version Control

The following files and patterns are excluded via `.gitignore`:
- `.env` files containing actual API keys and passwords
- Files with credentials in filenames (`*SECRETS*`, `*KEYS*`, `*CREDENTIALS*`)
- Archive directory (`_archive/`) containing files with real credentials
- Any files containing:
  - `YANDEX_API_KEY=AQVN...`
  - `MONGO_URI=mongodb+srv://user:password@...`
  - Database passwords
  - Access tokens

### Configuration

#### Local Development

Create a `.env` file (already in `.gitignore`):
```env
YANDEX_FOLDER_ID=your_folder_id
YANDEX_API_KEY=your_api_key
MONGO_URI=your_mongodb_uri
MONGO_DB=financial_career_coach
```

#### Production (Google Cloud Run)

Set environment variables via Cloud Console:
- Navigate to Cloud Run → Service → Edit & Deploy New Revision
- Add environment variables in the configuration section

### Pre-commit Verification

Before committing, verify no secrets are present:

```bash
grep -r "AQVN" . --exclude-dir=_archive
grep -r "mongodb+srv://.*:.*@" . --exclude-dir=_archive
```

If secrets are found, remove or replace with placeholders.

### Incident Response

If secrets are accidentally committed:
1. Immediately rotate all affected keys and passwords
2. Remove files from Git history using `git filter-branch` or `git filter-repo`
3. Update credentials in Cloud Run
4. Verify `.gitignore` patterns are correct










