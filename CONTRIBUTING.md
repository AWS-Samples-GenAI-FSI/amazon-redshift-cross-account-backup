# Contributing to ACA Redshift Cross-Account Backup Demo

Thank you for your interest in contributing to this project! This guide will help you get started.

## Development Setup

### Prerequisites
- Python 3.7+
- AWS CLI configured
- Two AWS accounts for testing
- Git

### Local Setup
```bash
# Clone the repository
git clone <repository-url>
cd aca-redshift-backup-demo

# Install dependencies
pip install -r requirements.txt

# Configure AWS profiles
aws configure --profile source
aws configure --profile target
```

## Project Structure

```
├── cloudformation/          # Infrastructure as Code
│   ├── source-account-setup.yaml
│   ├── target-account-setup.yaml
│   └── aca-lambda-backup-setup.yaml
├── scripts/                 # Demo and testing scripts
│   ├── native_snapshot_demo.py
│   └── aws_backup_demo.py
├── lambda/                  # Lambda function code
│   └── aca_redshift_backup_lambda.py
├── docs/                    # Documentation
│   ├── setup-guide.md
│   ├── comparison-analysis.md
│   └── lambda-automation-guide.md
├── *.sh                     # Deployment and utility scripts
└── requirements.txt         # Python dependencies
```

## Making Changes

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Include type hints where appropriate

### Testing
Before submitting changes:
1. Test with actual AWS resources (use development accounts)
2. Verify CloudFormation templates validate successfully
3. Run cleanup scripts to ensure proper resource removal
4. Test both source and target account operations

### Documentation
- Update relevant documentation for any feature changes
- Include examples for new functionality
- Update the comparison analysis if costs or features change
- Keep the README.md current with any new capabilities

## Submitting Changes

### Pull Request Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Pull Request Guidelines
- Provide a clear description of the changes
- Include the motivation for the changes
- List any breaking changes
- Add screenshots for UI changes (if applicable)
- Reference any related issues

## Reporting Issues

### Bug Reports
When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- AWS region and account setup details (anonymized)
- CloudFormation stack status and error messages
- Relevant log excerpts

### Feature Requests
For new features:
- Describe the use case
- Explain the expected behavior
- Consider the impact on existing functionality
- Suggest implementation approaches if possible

## Security

### Reporting Security Issues
Please do not report security vulnerabilities through public GitHub issues. Instead:
1. Email the maintainers directly
2. Provide detailed information about the vulnerability
3. Allow time for the issue to be addressed before public disclosure

### Security Best Practices
- Never commit AWS credentials or sensitive information
- Use least-privilege IAM policies
- Encrypt all data at rest and in transit
- Regularly review and rotate access keys
- Follow AWS security best practices

## Code of Conduct

### Our Standards
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professionalism in all interactions

### Unacceptable Behavior
- Harassment or discrimination
- Trolling or inflammatory comments
- Publishing private information
- Any conduct that would be inappropriate in a professional setting

## Getting Help

### Resources
- Check the documentation in the `docs/` directory
- Review existing issues and pull requests
- Consult AWS documentation for service-specific questions

### Contact
- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Email maintainers for security issues

## Development Guidelines

### AWS Resources
- Always use the `aca-` prefix for new resources
- Include appropriate tags for resource management
- Follow the established naming conventions
- Ensure proper cleanup in all scripts

### CloudFormation
- Validate templates before committing
- Use parameters for configurable values
- Include comprehensive outputs
- Add conditions for optional resources

### Lambda Functions
- Keep functions focused and single-purpose
- Include proper error handling
- Use environment variables for configuration
- Optimize for cost and performance

### Scripts
- Include usage instructions and examples
- Handle errors gracefully
- Provide clear status messages
- Support both interactive and automated execution

## Release Process

### Versioning
We use semantic versioning (SemVer):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Security review completed
- [ ] Performance impact assessed

Thank you for contributing to the ACA Redshift Cross-Account Backup Demo!