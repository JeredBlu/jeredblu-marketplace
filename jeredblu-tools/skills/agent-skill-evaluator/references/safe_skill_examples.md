# Safe Skill Examples

This document provides examples of legitimate skill patterns that might appear suspicious but are actually safe and appropriate for agent skills.

## Legitimate Complex Instructions

### Example 1: Comprehensive Workflow Management

**Pattern**:
```markdown
## Workflow Steps

### Step 1: Analysis Phase
When the user provides a document:
1. Read the document completely
2. Identify key sections and structure
3. Create a summary of main points
4. Store findings for later steps

### Step 2: Processing Phase  
Based on the analysis:
- If document type is X, follow procedure A
- If document type is Y, follow procedure B
- Otherwise, ask user for clarification

### Step 3: Output Generation
Create output according to user request while:
- Maintaining original formatting where appropriate
- Applying brand guidelines from assets/
- Including proper citations
```

**Why This is Safe**:
- Provides structured workflow for Claude to follow
- All actions serve the skill's stated purpose
- No attempts to override user intent or system safety
- Transparency about what skill will do

### Example 2: Conditional Behavior Based on Context

**Pattern**:
```markdown
## Adaptive Response Strategy

The skill should adapt its approach based on the query complexity:
- For simple queries: Provide direct answers without extensive research
- For complex queries: Execute multi-step research process
- For ambiguous queries: Ask clarifying questions before proceeding

When documents are attached:
- First verify file type compatibility
- Then apply appropriate processing method
- Finally present results in requested format
```

**Why This is Safe**:
- Legitimate contextual adaptation to serve user better
- Conditions are based on task complexity, not hidden triggers
- All behaviors support the skill's documented purpose
- No data exfiltration or permission escalation

### Example 3: Multi-File Coordination

**Pattern**:
```markdown
## Resource Management

This skill uses multiple reference files. Load them as follows:
- For schema questions: Read references/database_schema.md
- For API questions: Read references/api_documentation.md  
- For examples: Read references/code_examples.md

If encountering errors:
1. Check references/troubleshooting.md
2. Document the specific error
3. Attempt fallback approaches
4. Inform user of limitations if unresolved
```

**Why This is Safe**:
- Legitimate use of skill's bundled resources
- Follows progressive disclosure principles
- Error handling is transparent and documented
- No hidden behaviors or unauthorized actions

## Legitimate File Operations

### Example 1: Template Processing

**Pattern**:
```python
import os
import shutil

def process_template(template_name, output_path):
    """Copy and customize template from assets."""
    template_path = os.path.join('assets', 'templates', template_name)
    
    # Verify template exists
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template {template_name} not found")
    
    # Copy to output location
    shutil.copy(template_path, output_path)
    
    # Customize as needed
    customize_file(output_path)
```

**Why This is Safe**:
- Only accesses bundled assets (not system files)
- File paths are validated
- Operations are limited to skill's intended functionality
- No unauthorized file system access

### Example 2: Document Processing

**Pattern**:
```python
def read_user_document(filepath):
    """Read document uploaded by user."""
    # Validate file is in expected location
    if not filepath.startswith('/mnt/user-data/uploads/'):
        raise ValueError("File must be in uploads directory")
    
    # Read and process
    with open(filepath, 'r') as f:
        content = f.read()
    
    return process_content(content)
```

**Why This is Safe**:
- Validates file location before access
- Only reads from user-uploaded files
- Clear purpose aligned with skill functionality
- No access to system or sensitive files

## Legitimate Network Operations

### Example 1: API Documentation Access

**Pattern**:
```python
import requests

def fetch_api_docs(api_version):
    """Fetch official API documentation."""
    official_docs_url = f"https://docs.example-api.com/v{api_version}"
    
    response = requests.get(official_docs_url)
    response.raise_for_status()
    
    return response.json()
```

**Why This is Safe**:
- Accesses official, documented API
- Purpose is clearly to retrieve documentation
- No user data being sent
- URL is predictable and verifiable

### Example 2: Version Checking

**Pattern**:
```python
def check_for_updates():
    """Check if newer version of skill available."""
    repo_url = "https://api.github.com/repos/creator/skill-name/releases/latest"
    
    try:
        response = requests.get(repo_url)
        latest = response.json()
        return latest.get('tag_name')
    except Exception:
        # Fail silently if unable to check
        return None
```

**Why This is Safe**:
- Checks for updates from official source
- No data collection or transmission
- Failure is handled gracefully
- User is informed of version checks

## Legitimate Code Execution

### Example 1: Sandboxed Script Execution

**Pattern**:
```python
def run_analysis_script(input_data):
    """Execute bundled analysis script safely."""
    script_path = 'scripts/data_analyzer.py'
    
    # Run in controlled environment
    result = subprocess.run(
        ['python', script_path],
        input=input_data,
        capture_output=True,
        text=True,
        timeout=30,  # Prevent hanging
        cwd='/home/claude'  # Controlled working directory
    )
    
    return result.stdout
```

**Why This is Safe**:
- Only executes bundled, reviewed scripts
- Uses timeout to prevent DoS
- Runs in controlled directory
- Captures output without system access

### Example 2: Data Transformation

**Pattern**:
```python
import json

def transform_data(input_json):
    """Transform user data according to schema."""
    data = json.loads(input_json)
    
    # Apply transformations
    transformed = {
        'processed_at': datetime.now().isoformat(),
        'results': process_records(data['records']),
        'summary': generate_summary(data)
    }
    
    return json.dumps(transformed, indent=2)
```

**Why This is Safe**:
- Pure data transformation
- No system calls or network access
- Clear, documented purpose
- Operates only on provided data

## Distinguishing Safe from Malicious

### Safe Pattern Characteristics:
1. **Transparent**: Purpose is clearly documented
2. **Bounded**: Operations limited to skill's scope
3. **Validated**: Inputs are checked and sanitized
4. **Reversible**: Actions don't create persistent changes
5. **Aligned**: Behavior matches stated functionality

### Malicious Pattern Characteristics:
1. **Hidden**: Undocumented or obfuscated behavior
2. **Unbounded**: Access beyond necessary scope
3. **Unvalidated**: Accepts arbitrary inputs
4. **Persistent**: Creates lasting changes or backdoors
5. **Misaligned**: Behavior contradicts stated purpose

## Edge Cases

### Case 1: Sophisticated Workflow Instructions

A skill with 50+ steps for document processing might look suspicious due to complexity, but is likely safe if:
- Each step serves documented purpose
- No steps attempt to override user intent
- Workflow is transparent and logical
- Error handling is appropriate

### Case 2: Environment Variable Usage

Reading environment variables isn't inherently malicious if:
- Variables are for configuration (not credentials)
- Usage is documented in skill description
- Variables are optional with safe defaults
- Skill doesn't transmit environment data

### Case 3: Dynamic Code Generation

Generating code dynamically can be safe if:
- Generation is based on templates (not arbitrary execution)
- Generated code serves skill's stated purpose
- User has visibility into what's generated
- No exec() or eval() on untrusted input

## Red Flags Even in "Safe-Looking" Code

1. **Mismatch**: Code that doesn't align with skill description
2. **Obfuscation**: Unnecessary complexity or encoding
3. **Hidden URLs**: Network requests to undocumented endpoints
4. **Credential Access**: Reading auth tokens, API keys, passwords
5. **Privilege Requests**: Asking for unnecessary permissions

## When in Doubt

If a pattern seems suspicious:
1. Check if it's documented in SKILL.md
2. Assess if it's necessary for stated functionality
3. Verify no data is being exfiltrated
4. Look for legitimate alternatives
5. Consider creator's reputation and transparency

Remember: Complexity ≠ Malicious, but Hidden Intent = Dangerous
