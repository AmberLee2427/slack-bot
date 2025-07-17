# Repository Management Scripts

This directory contains scripts for managing the knowledge base repositories.

## Quick Start

### 1. List all configured repositories
```bash
python scripts/manage_repositories.py --list
```

### 2. Refresh all repositories (clone new ones, update existing ones)
```bash
python scripts/manage_repositories.py
```

### 3. Update only a specific category
```bash
python scripts/manage_repositories.py --category microlensing_tools
```

### 4 Clean up orphaned repositories (dry run)
```bash
python scripts/manage_repositories.py --clean --dry-run
```

### 5ally remove orphaned repositories
```bash
python scripts/manage_repositories.py --clean
```

## Configuration

The repositories are defined in `config/repositories.yml`. You can edit this file to:

- Add new repositories
- Remove repositories you don't need
- Change repository URLs
- Add custom categories

## Repository Categories

- **microlensing_tools**: Analysis tools and libraries
- **general_tools:** Astronomy and Roman related tools
- **jupyter_notebooks**: Tutorial notebooks and examples
- **web_resources**: Documentation and web content

## How It Works

1**Initial Setup**: The script clones repositories that dont exist locally
2. **Updates**: For existing repositories, it runs `git fetch` and `git pull` to get the latest changes3 **Organization**: Repositories are organized by category in `knowledge_base/raw/`
4**Configuration**: Uses YAML configuration for easy management

## Benefits of This Approach

- **Easy Refresh**: Just run the script to get the latest versions of all repositories
- **No Manual Work**: No need to manually clone or update repositories
- **Version Control**: Git handles all the version management
- **Flexible**: Easy to add/remove repositories by editing the config file
- **Clean**: Can remove repositories that are no longer needed

## Example Workflow

```bash
# 1. Check what repositories are configured
python scripts/manage_repositories.py --list

# 2. Refresh all repositories to latest versions
python scripts/manage_repositories.py

# 3. Check for any orphaned repositories
python scripts/manage_repositories.py --clean --dry-run

# 4 youre happy with the changes, actually clean up
python scripts/manage_repositories.py --clean
```

This approach is much better than manually cloning repositories because:
- You can easily refresh everything with one command
- The configuration is version controlled
- You can see exactly what repositories are being tracked
- Its easy to add new repositories or remove old ones 