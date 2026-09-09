# Repository secrets

The workflow uses GitHub's built-in `GITHUB_TOKEN` to commit generated profile files.

To inventory **all original repositories**, including private repositories, add one additional repository secret to `qselmer/qselmer`:

- Name: `PROFILE_REPO_TOKEN`
- Recommended credential: fine-grained personal access token
- Resource owner: `qselmer`
- Repository access: all repositories
- Permissions: read-only repository metadata/content required to list repositories and topics; no write permission is needed

The workflow has `INCLUDE_PRIVATE_REPOS: "true"`. If `PROFILE_REPO_TOKEN` is missing, the script falls back safely to public original repositories only.

Private repositories are used for the complete **Repository Types** count and internal portfolio inventory. Their names, descriptions, languages and update dates are **not rendered in the public README tables**. The public detailed repository portfolio remains restricted to active public originals.
