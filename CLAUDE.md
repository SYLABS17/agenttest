# CLAUDE.md - AI Assistant Guide

## Repository Overview

**Repository**: agenttest
**Purpose**: Test repository for AI assistant development workflows
**Current State**: Initial setup phase
**Last Updated**: 2025-11-17

This repository is currently in its initial state and serves as a testing ground for establishing development workflows, conventions, and best practices for AI-assisted software development.

---

## Table of Contents

1. [Repository Structure](#repository-structure)
2. [Development Workflow](#development-workflow)
3. [Git Conventions](#git-conventions)
4. [Code Conventions](#code-conventions)
5. [AI Assistant Guidelines](#ai-assistant-guidelines)
6. [Testing Strategy](#testing-strategy)
7. [Documentation Standards](#documentation-standards)

---

## Repository Structure

### Current Structure

```
agenttest/
├── .git/                 # Git repository metadata
└── CLAUDE.md            # This file - AI assistant guide
```

### Planned Structure

As the repository grows, the following structure is recommended:

```
agenttest/
├── .git/                 # Git repository metadata
├── .github/              # GitHub-specific configuration
│   └── workflows/        # CI/CD workflows
├── src/                  # Source code
│   ├── components/       # Reusable components
│   ├── utils/           # Utility functions
│   ├── services/        # Business logic/services
│   └── index.js         # Entry point
├── tests/                # Test files
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
├── docs/                 # Additional documentation
├── config/              # Configuration files
├── .gitignore           # Git ignore rules
├── README.md            # Project overview and setup
├── CLAUDE.md            # AI assistant guide (this file)
├── CONTRIBUTING.md      # Contribution guidelines
├── LICENSE              # License information
└── package.json         # Project dependencies (if Node.js)
```

---

## Development Workflow

### Branch Strategy

This repository follows a feature branch workflow:

1. **Main Branch**: `main` or `master` (protected)
   - Contains production-ready code
   - Requires pull request reviews before merging
   - Should always be in a deployable state

2. **Feature Branches**: `claude/<session-id>` or `feature/<feature-name>`
   - Created from main branch
   - Used for developing new features or fixes
   - Named descriptively to indicate purpose
   - Merged back to main via pull request

### Development Process

1. **Start**: Create or checkout feature branch
2. **Develop**: Make changes following code conventions
3. **Test**: Ensure all tests pass
4. **Commit**: Write clear, descriptive commit messages
5. **Push**: Push to remote feature branch
6. **Review**: Create pull request for code review
7. **Merge**: Merge to main after approval

---

## Git Conventions

### Commit Messages

Follow the conventional commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples**:
```
feat(auth): add user authentication system

Implement JWT-based authentication with login and logout endpoints.
Includes password hashing and token validation.

Closes #123
```

```
fix(api): resolve null pointer exception in user service

Add null check before accessing user object properties.
```

### Branch Naming

- Feature branches: `feature/<descriptive-name>` or `claude/<session-id>`
- Bug fixes: `fix/<issue-description>`
- Hotfixes: `hotfix/<critical-issue>`
- Experimental: `experiment/<name>`

### Pull Request Guidelines

1. **Title**: Clear, concise description of changes
2. **Description**: Include:
   - Summary of changes
   - Motivation and context
   - Testing performed
   - Screenshots (if UI changes)
   - Related issues/tickets
3. **Reviews**: At least one approval required
4. **CI/CD**: All checks must pass
5. **Conflicts**: Resolve before merging

---

## Code Conventions

### General Principles

1. **Clarity over Cleverness**: Write code that is easy to understand
2. **DRY (Don't Repeat Yourself)**: Avoid code duplication
3. **SOLID Principles**: Follow object-oriented design principles
4. **Separation of Concerns**: Keep different functionalities separate
5. **Error Handling**: Always handle errors gracefully

### Code Style

#### File Naming
- Use lowercase with hyphens for files: `user-service.js`
- Use PascalCase for classes: `UserService`
- Use camelCase for variables and functions: `getUserData()`

#### Code Organization
- One class/component per file
- Group related functions together
- Keep files under 300 lines when possible
- Extract complex logic into separate functions

#### Comments and Documentation
- Use comments to explain "why", not "what"
- Document complex algorithms
- Add JSDoc/docstrings for public APIs
- Keep comments up-to-date with code

#### Variables and Naming
- Use descriptive names: `userAuthentication` not `ua`
- Boolean variables: `isActive`, `hasPermission`, `canEdit`
- Constants: `UPPERCASE_WITH_UNDERSCORES`
- Private variables: prefix with underscore `_privateVar`

### Security Best Practices

1. **Input Validation**: Always validate and sanitize user input
2. **SQL Injection**: Use parameterized queries
3. **XSS Prevention**: Escape output, use Content Security Policy
4. **Authentication**: Use proven libraries, never roll your own crypto
5. **Secrets**: Never commit secrets, API keys, or passwords
6. **Dependencies**: Keep dependencies updated, audit regularly
7. **OWASP Top 10**: Be aware of common vulnerabilities

---

## AI Assistant Guidelines

### When Working in This Repository

#### 1. Understanding Context
- **Always** read relevant files before making changes
- Use Glob and Grep tools to search the codebase
- Check existing patterns and conventions
- Review recent commits to understand ongoing work

#### 2. Planning and Tracking
- **Always** use TodoWrite tool for multi-step tasks
- Break down complex tasks into manageable steps
- Mark tasks as in_progress before starting
- Mark tasks as completed immediately after finishing
- Keep only ONE task in_progress at a time

#### 3. Code Changes
- **Prefer editing** existing files over creating new ones
- Read files before editing to understand context
- Follow existing code style and conventions
- Add appropriate error handling
- Write secure code (no SQL injection, XSS, etc.)
- Test changes after implementation

#### 4. Git Operations
- Develop on designated feature branches
- Use clear, descriptive commit messages
- Push to remote with: `git push -u origin <branch-name>`
- Branch names must start with `claude/` for this project
- Never push to main/master without permission
- If push fails, retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s)

#### 5. Communication
- Be concise and clear in responses
- Reference code with `file_path:line_number` format
- Output text directly, never use echo/printf
- Avoid emojis unless explicitly requested
- Focus on facts and technical accuracy

#### 6. Tool Usage
- Use specialized tools over bash commands
- Read files with Read tool, not cat
- Edit files with Edit tool, not sed/awk
- Use Task tool with Explore agent for codebase exploration
- Run independent tool calls in parallel
- Never guess or use placeholders for tool parameters

#### 7. Problem Solving
- Research before implementing
- Understand the "why" before the "how"
- Consider edge cases and error scenarios
- Test incrementally
- Ask for clarification when requirements are unclear

### Common Pitfalls to Avoid

❌ **Don't**:
- Create unnecessary files (especially markdown/docs)
- Use bash for file reading/editing operations
- Batch multiple task completions
- Amend commits from other developers
- Push to wrong branches
- Commit secrets or sensitive data
- Skip error handling
- Write insecure code
- Make assumptions without verification

✅ **Do**:
- Use appropriate specialized tools
- Complete tasks fully before marking done
- Write clear commit messages
- Follow security best practices
- Ask questions when unclear
- Test your changes
- Document complex logic
- Keep the user informed of progress

---

## Testing Strategy

### Test Pyramid

1. **Unit Tests** (70%)
   - Test individual functions and components
   - Fast, isolated, focused
   - Mock external dependencies

2. **Integration Tests** (20%)
   - Test component interactions
   - Verify system integration points
   - Use test databases/services

3. **End-to-End Tests** (10%)
   - Test complete user workflows
   - Slower but high confidence
   - Run before releases

### Testing Best Practices

- Write tests for new features
- Maintain high code coverage (>80%)
- Keep tests fast and independent
- Use descriptive test names
- Follow AAA pattern: Arrange, Act, Assert
- Mock external services
- Test edge cases and error scenarios

### Running Tests

```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run with coverage
npm run test:coverage

# Watch mode for development
npm run test:watch
```

---

## Documentation Standards

### README.md

Every project should have a comprehensive README:

1. **Project Title and Description**
2. **Installation Instructions**
3. **Usage Examples**
4. **Configuration**
5. **API Documentation** (if applicable)
6. **Contributing Guidelines**
7. **License**
8. **Contact Information**

### Code Documentation

- Public APIs: Full documentation with parameters, return values, examples
- Complex Logic: Inline comments explaining approach
- Modules: Header comments explaining purpose
- Changes: Update docs when code changes

### CLAUDE.md Updates

This file should be updated when:
- Project structure changes significantly
- New conventions are adopted
- Development workflow evolves
- New tools or frameworks are introduced
- Best practices are identified

---

## Quick Reference

### Essential Commands

```bash
# Check current branch and status
git status

# Create and switch to feature branch
git checkout -b claude/<session-id>

# Stage and commit changes
git add .
git commit -m "feat: descriptive message"

# Push to remote
git push -u origin claude/<session-id>

# View recent commits
git log --oneline -10

# See what changed
git diff
```

### File References in Code

When referencing code locations, use format: `file_path:line_number`

Example: "The authentication logic is in src/services/auth-service.js:45"

---

## Additional Resources

### Documentation
- Project README: `README.md` (to be created)
- Contributing Guide: `CONTRIBUTING.md` (to be created)
- API Docs: `docs/api.md` (to be created)

### External Links
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Clean Code Principles](https://github.com/ryanmcdermott/clean-code-javascript)

---

## Maintenance

### Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-17 | 1.0.0 | Initial CLAUDE.md creation |

### Contributors

- AI Assistant: Initial documentation setup

---

## Notes for Future Development

As this repository evolves, consider:

1. **Technology Stack**: Define primary languages, frameworks, and tools
2. **Architecture**: Document system architecture and design decisions
3. **Dependencies**: Maintain up-to-date dependency list
4. **Performance**: Establish performance benchmarks and optimization guidelines
5. **Deployment**: Document deployment processes and environments
6. **Monitoring**: Add logging and monitoring strategies
7. **Security**: Implement security scanning and vulnerability management

---

*This document is a living guide that should evolve with the repository. Keep it updated and relevant.*
