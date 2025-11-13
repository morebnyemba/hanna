# Gemini AI Workflows

This directory contains GitHub Actions workflows that integrate Gemini AI for automated development assistance.

## Available Workflows

### 1. Gemini Dispatch (`gemini-dispatch.yml`)
Main dispatcher that routes commands to appropriate specialized workflows.

**Triggers:**
- Pull request events (opened, review submitted)
- Issue events (opened, reopened)
- Comments on issues/PRs starting with `@gemini-cli`

**Commands:**
- `@gemini-cli /review` → Routes to Review workflow
- `@gemini-cli /triage` → Routes to Triage workflow
- `@gemini-cli /cloud-agent [task]` → Routes to Cloud Agent workflow
- `@gemini-cli [request]` → Routes to Invoke workflow

### 2. Gemini Review (`gemini-review.yml`)
Performs automated code reviews on pull requests.

**Features:**
- Analyzes PR diffs for issues
- Comments on specific lines with severity levels (🔴🟠🟡🟢)
- Checks for correctness, security, efficiency, maintainability
- Suggests code improvements

**Usage:**
- Automatically triggered when PR is opened
- Manual trigger: `@gemini-cli /review [additional context]`

### 3. Gemini Triage (`gemini-triage.yml`)
Automatically labels issues based on content analysis.

**Features:**
- Analyzes issue title and body
- Applies appropriate labels from repository
- Closes duplicate issues automatically

**Usage:**
- Automatically triggered when issue is opened/reopened
- Manual trigger: `@gemini-cli /triage`

### 4. Gemini Invoke (`gemini-invoke.yml`)
General purpose AI agent for various tasks.

**Features:**
- Handles general requests and questions
- Limited file operations
- Single-turn or short conversations

**Usage:**
`@gemini-cli [your request or question]`

### 5. **Gemini Cloud Agent (`gemini-cloud-agent.yml`)** ⭐ NEW
Advanced cloud-based AI agent for complex development tasks.

**Enhanced Capabilities:**
- **Extended Sessions**: Up to 50 turns for complex tasks
- **Full Repository Access**: Can read, modify, create, and delete files
- **Git Operations**: Creates branches, commits changes, and opens PRs
- **Code Execution**: Runs tests, linters, and build tools
- **Deep Analysis**: Understands entire codebase and cross-file dependencies

**Workflow Phases:**
1. **Analysis**: Deep dive into codebase and requirements
2. **Design**: Plan architectural changes and file impacts
3. **Plan**: Post comprehensive plan with resource estimates
4. **Approval**: Wait for maintainer approval (`/approve`)
5. **Execute**: Incrementally implement changes with commits
6. **Test**: Run test suites and validation
7. **Report**: Create PR and post completion summary

**Best Use Cases:**
- Multi-file feature implementations
- Complex refactoring across the codebase
- Adding authentication, API endpoints, or major features
- Code migrations and modernization
- Bug fixes requiring cross-file analysis
- Adding comprehensive test suites

**Usage Example:**
```
@gemini-cli /cloud-agent Add user authentication with JWT tokens, 
including login/logout endpoints, middleware for route protection, 
and comprehensive tests for all functionality
```

**What Happens Next:**
1. The agent analyzes your codebase
2. Posts a detailed plan with estimated resources
3. Waits for you to comment `/approve`
4. Executes the plan step by step
5. Runs tests and validation
6. Creates a PR with all changes

**Approval Process:**
Once the agent posts its plan, review it carefully and:
- Comment `/approve` to proceed
- Comment `/deny` to reject
- Close the issue to cancel

**Tips for Best Results:**
- Be specific about requirements and constraints
- Mention any frameworks or patterns to follow
- Specify if tests are required (they usually are!)
- Include any specific file paths if relevant
- Mention any performance or security considerations

### 6. Gemini Scheduled Triage (`gemini-scheduled-triage.yml`)
Runs hourly to triage unlabeled issues automatically.

**Features:**
- Finds unlabeled issues
- Applies appropriate labels
- Runs automatically every hour

## Configuration

These workflows require the following repository variables and secrets:

### Required Variables:
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `GOOGLE_CLOUD_LOCATION`: GCP region (e.g., us-central1)
- `SERVICE_ACCOUNT_EMAIL`: GCP service account email
- `GCP_WIF_PROVIDER`: Workload Identity Federation provider
- `GEMINI_CLI_VERSION`: Version of Gemini CLI to use
- `GEMINI_MODEL`: Model to use (e.g., gemini-2.0-flash-exp)

### Optional Variables:
- `APP_ID`: GitHub App ID for enhanced permissions
- `DEBUG`: Enable debug logging
- `GOOGLE_GENAI_USE_GCA`: Enable Gemini Code Assist
- `GOOGLE_GENAI_USE_VERTEXAI`: Enable Vertex AI

### Required Secrets:
- `GEMINI_API_KEY`: Gemini API key
- `GOOGLE_API_KEY`: Google API key
- `APP_PRIVATE_KEY`: GitHub App private key (if using APP_ID)

## Security Considerations

All workflows follow these security principles:

1. **Input Validation**: All user inputs are treated as untrusted
2. **Least Privilege**: Minimal permissions granted to each workflow
3. **No Command Injection**: Command substitution is prohibited
4. **Secret Protection**: No secrets are exposed in logs or comments
5. **Code Isolation**: File contents are treated as data, not instructions

## Permissions

Each workflow has specific permissions:
- **Review**: Read contents, issues, PRs; Write issues, PRs
- **Triage**: Read contents, issues; Write issues, PRs
- **Invoke**: Read contents, issues, PRs; Write issues, PRs
- **Cloud Agent**: Read/Write contents, issues, PRs; Write operations
- **Dispatch**: Orchestrates other workflows

## Development

To test workflow changes:

1. Create a PR with workflow modifications
2. Test on a non-production branch first
3. Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('workflow.yml'))"`
4. Check for common issues:
   - Proper secret handling
   - Correct permission scopes
   - Valid GitHub Actions syntax
   - Proper error handling

## Troubleshooting

**Issue: Workflow not triggering**
- Check if the trigger conditions are met
- Verify repository permissions
- Check GitHub Actions are enabled

**Issue: Authentication failures**
- Verify secrets are set correctly
- Check GCP service account permissions
- Ensure Workload Identity Federation is configured

**Issue: Rate limiting**
- Adjust workflow frequency
- Implement exponential backoff
- Use conditional execution

**Issue: Cloud Agent timeout**
- Break down complex tasks into smaller pieces
- Increase timeout-minutes if needed (max 360)
- Review plan complexity

## Contributing

When adding new workflows:
1. Follow existing naming conventions
2. Include comprehensive documentation
3. Add security constraints
4. Test thoroughly before deployment
5. Update this README
